# Unequal V2G efficiencies: bounded analytical assessment

Source-only proof/counterexample assessment of the current lossless two-batch model. No imports, execution, numerical tests, cohort, native work, source edits or new agents. **The lossless `(E,S-E,fee)` representation does not survive round-trip loss.** A meaningful restricted extension is possible, but an exact general threshold/hull theorem is not established here.

## Correct accounting before any projection

Let charging efficiency be `0<eta_c<=1` and discharging efficiency `0<eta_d<=1`, constant across buses/windows. Let C_v>=0 be early grid purchases and D_v>=0 early grid exports. Battery exchange is

`x_v=eta_c*C_v-D_v/eta_d`.

Do not identify x_v with net grid energy. With full initial/final inventories and total service consumption S, terminal **grid** purchases satisfy

`L=(S-sum x_v)/eta_c`.

Writing C=sum C_v, D=sum D_v and E=C-D gives

`L=S/eta_c-E+(1/(eta_c*eta_d)-1)*D`.

Thus total net grid purchase is `S/eta_c+kappa*D`, where kappa>0 under strict round-trip loss. E alone does not determine L. Equal buy/sell tariffs do not remove this physical loss term. If both directions have grid-side power K in the early unit window, gross connector occupancy is `(C+D)/K`, not `|E|/K` and not `sum |x_v|/K`. With distinct grid-side directional powers, occupancy is `C/K_c+D/K_d`.

## Exact hand counterexample

Take one A service and one B service, each consumption1, battery capacity2, and two standalone buses. Let eta_c=eta_d=1/2, shared early grid power K1 and terminal grid power H6, with the same common windows and full start/end. Both plans use two buses and have net early grid load E0.

- No early action: each bus needs1 battery unit terminally, hence2 grid units; total terminal L4.
- Charge the A bus by1/2 grid unit and discharge the B bus by1/2 grid unit. These serialize in the early hour (half an hour each at power1). A gains1/4 battery unit; B loses1 battery unit. After their remaining services, A has5/4 and B has0. Terminal battery refills are3/4 and2, hence grid refills3/2 and4: **L=11/2**. These serialize within the terminal hour at power6 and restore both batteries to2.

The same E and operating fee therefore have different terminal loads4 and11/2. Even replacing S by the no-discharge loss-adjusted baseline S/eta_c does not restore the old affine line. This refutes direct transfer of both the lossless total-energy identity and its interval formula in net-grid coordinates. The second point is dominated at fixed E if terminal supply cost is nondecreasing; that does not make the complete physical projection a line.

## What nonnegative prices/marginals do permit

In a common early window, a bus with both C_v>0 and D_v>0 can have a battery-neutral cycle removed. Reduce C_v by delta and D_v by eta_c*eta_d*delta, choosing delta to zero one direction. This preserves x_v and every service/terminal endpoint, reduces connector time, and reduces early net grid purchase by `(1-eta_c*eta_d)*delta`. Because all early availability is common and a monotone action realizes any endpoint between the valid SOC bounds, the replacement is physically feasible.

With nonnegative posted early prices, or a planner supply objective nondecreasing in early grid load with terminal load fixed, such within-bus cycles are weakly dominated. Strict loss and a positive marginal give strict improvement. This supports an **optimal-value reduction**, not equality of complete physical sets; at zero prices unnecessary cycles may tie. Negative prices, throughput subsidies or asymmetric settlement require separate analysis. Across-bus charging and discharging cannot in general be removed this way: mandatory positive recharge on a paired bus may coexist with discharge from a different bus.

For a cycle-free allocation, the battery-coordinate boxes remain the lossless boxes, but

`C_v=(x_v)_+/eta_c`, `D_v=eta_d*(-x_v)_+`.

The exact physical conditions become those boxes together with

`sum[(x_v)_+/eta_c+eta_d*(-x_v)_+]<=K`,
`L=(S-sum x_v)/eta_c<=H`,
`E=sum[(x_v)_+/eta_c-eta_d*(-x_v)_+]`.

These are a safe starting formulation for cycle-free optimization under the stated monotonicity. Positive and negative battery exchanges are **not independently selectable**: each bus has one sign or zero. Replacing them by two unrelated aggregate nonnegative variables can falsely allow a single bus to supply both. Enumerating bus sign patterns gives a finite union of rational polytopes for fixed matching and rational efficiencies; projecting those polytopes into `(E,L,fee)` is exact for the cycle-free reduction. It is not yet the old cardinality-threshold theorem.

## Minimal honest generalized claim and next action

Proven here: accounting identity; explicit failure of the one-dimensional lossless projection; and dominance of within-bus early cycles for optimal values under nonnegative prices/marginals and common-window physics. The natural representation is a **joint early/terminal grid-load–vehicle-cost frontier**, equivalently including exported throughput D. One can sometimes reduce it further after optimizing a monotone objective, but such a scalar envelope need not have the old affine supply argument or matching thresholds.

Open: a complete efficient-frontier formula, sufficient matching statistics, discrete convexity and support classification with losses. Before a broad theorem, the useful next analytical step is a fixed-matching sign-pattern projection and a small exact example in which discharging is genuinely efficient under a declared supply objective. If that only yields a cumbersome union without a new structural insight, report losslessness as a material scope limitation rather than adding an unproved “efficiency robustness” claim. No public V2G or empirical claim follows.
