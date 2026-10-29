# Complete assignment-graph extension: independent analytical review

**Verdict: PASS under the explicitly stated ideal common-window, compulsory-transition, charge-only model.** No counterexample was found. This is an analytical result, not implementation qualification or a road-metric realization. I read the current exponential-transition appendix and checked the proposed new edges independently; no data or execution was used.

Let `h_i=B/2+3w_i`, `l_i=w_i`, `W=sum w_i`, `K=kB/2+4W`, `Smax=kB+20W`, and use `H=2kB`. Keep the fleet cap `2k` and the two simultaneous batches of `2k` services. Therefore every feasible service plan has exactly `2k` buses and a perfect matching. Idle buses, singleton duties, or a second service within either simultaneous batch cannot evade this conclusion. All new edges must be time-feasible compulsory noncharging tasks in the same transition window; completeness means assignment-graph completeness, not unrestricted movement choices.

## Physical feasibility of every perfect matching

For an edge `i->j`, write `e=a_i+b_j+d_ij` and `r=max(0,e-B)`. Its early purchase interval is `[r,a_i]`, provided its post-early consumption `b_j+d_ij<=B`.

- Within a block this holds for identity and cross edges: the largest cross post-early consumption is `B/2+9w_i<=B`.
- For an interblock edge, `d_ij=B-b_j>=0`, so post-early consumption is exactly `B`, `e=a_i+B`, and `r=a_i`. That bus must refill fully in the early window.

Thus all edge intervals are nonempty. A perfect matching admits total early purchases `[R,K]`, where `R=sum r`. In particular full early refill `E=K` always works. Each bus's terminal requirement at any feasible early choice is at most `B`, so `H=2kB` accommodates **every** matching at every `E` in this interval, not merely the full-refill point. Serial early/terminal charging is feasible with the stated unit windows, shared power/budgets K and H, and per-bus acceptance at least those powers. Nonnegative task draw throughout and no in-task charging make endpoint SOC bounds sufficient. Initial and terminal SOC are full.

Consequently each matching has the complete physical branch `L=S-E`, `R<=E<=K`, with constant cost `2kf`, where `S=sum e`. No claim that different matchings have the old branch formulas is needed.

## Global affine certificate, including all new edges

Give each high A/B service potential `B/2+9w_i` and each low A/B service potential `w_i`. Their total over all services is `Smax`. For edge cost `c_ij=e_ij+2r_ij`, **every within-block edge is tight**:

- high/high: `c=B+18w_i`;
- low/low: `c=2w_i`;
- either cross: `c=B/2+10w_i`.

For an interblock edge, `c=3a_i+B`. If its origin is low, the slack against `u_i+v_j` is either `B/2+2w_i-9w_j` (high destination) or `B+2w_i-w_j` (low destination). If its origin is high, it is `3B/2-9w_j` (high destination) or `2B-w_j` (low destination). Under `B>=20 wmax`, every such slack is at least `wmax+2wmin` (the low-to-high bound is the limiting one). Hence

`S+2R >= Smax`,

with equality for within-block matchings, and excess at least `wmax+2wmin>=3` for a matching containing any interblock edge. This is an explicit feasible linear-assignment dual certificate; it does not assume the desired matching is optimal.

For any physical schedule, `E>=R`, so `3E+L=S+2E>=Smax`. The same affine inequality holds on all complete-plan mixtures.

## Exact physical and hull values

For `F=3E+L+(E-3)^2/(2K)`, nonnegative loads and `K>=14` give positive coordinate derivatives. The old within-block corners R=0 and R=6 remain feasible with the enlarged H. Their equal mixture has `(E,L)=(3,Smax-9)`, so

`CH=Smax+2kf`.

Within-block matchings retain the old complete branches; their physical minimum is attained exactly at R=0 and R=6, with excess `9/(2K)`. For any interblock matching and any of its schedules,

`F+2kf >= Smax+2kf+(wmax+2wmin)`.

Since `9/(2K)<=9/28<1<3`, no such schedule can attain the physical minimum. Therefore the **entire complete-graph opportunity set**, under the fleet cap and stated timing/physics, has

`D=CH+9/(2K)>CH`.

The unique projected hull optimum and the two minimizing physical corners follow as before. The classical support implication applies; there is no missing alternative matching in this argument.

## What survives, and what must not be claimed

Every old corner also remains the unique projected optimum for its old selector `3E+L+epsilon(E-R*)^2`: within-block equality selects that corner, whereas any interblock matching has affine excess at least three. Thus all `2^k` selected physical corners survive. This does **not** establish that the whole efficient frontier or every old efficient segment is unchanged; interblock branches must be included when describing the complete frontier.

The capacity and connector powers scale with k, all transition edges are compulsory ideal tasks, and there is no metric/geographical realization claim. The result removes disconnection of the allowed assignment graph as an explanation of this example. It does not remove the fleet cap, common-window assumptions, nonregenerative charge-only physics, or the dependence of gap magnitude on K; nor does it establish generic hardness, exponentially many hull vertices, or robustness to arbitrary additional routing options.
