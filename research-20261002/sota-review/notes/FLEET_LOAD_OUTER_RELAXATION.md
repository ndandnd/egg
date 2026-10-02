# Fleet load outer relaxation: stock and charging opportunity

2 October 2026. Theoretical package only; no model/data inspection, optimization or cluster work. These are conditional necessary constraints and standard relaxation arguments, not a new theorem or verified EGG formulation.

## Explicit assumptions and retained stock model

Fix fleet membership over epochs \(0,\ldots,T\), with \(N\) homogeneous batteries of capacity \(C\), mandatory reserve \(r\), and usable capacity \(U=C-r>0\). Let \(s_t\) be aggregate energy above reserve, so \(0\le s_t\le NU\). For heterogeneous batteries use their capacity sum, or a proven outer bound \(NU_{\max}\). Reserve conventions and fleet entry/exit must match the physical model.

Let \(a_{jt}\ge0\) denote grid energy purchased at station \(j\) in epoch \(t\), \(e_t=\sum_j a_{jt}\), and \(q_t=\sum_j\eta_j a_{jt}\) battery-side charging, with known linear efficiencies \(0<\eta_j\le1\). Mandatory service withdrawals \(d_t\ge0\) must be exogenous amounts assigned to these epochs, or valid lower envelopes of actual withdrawals. Write additional withdrawals as \(h_t\ge0\), including route-dependent deadhead and any unrepresented nonnegative losses. Assume no export, regeneration offset, or gratuitous energy disposal unless separately and correctly accounted for.

Every physical schedule then projects into
\[
s_t=s_{t-1}+q_t-d_t-h_t,\quad
L_t(N)\le s_t\le U_t(N),\quad h_t\ge0,
\]
where the basic bounds are \(L_t=0,U_t=NU\), and known initial/terminal stocks may tighten them. A valid deadhead upper envelope \(h_{a+1}+\cdots+h_b\le\bar H_{ab}\) can be added if proved. Allowing unrestricted \(h\) relaxes the model, including fictitious dissipation; it is safe but loses charging upper constraints. Do not invent \(\bar H\) from observed routes.

Station envelopes \(0\le a_{jt}\le\bar A_{jt}\) must cover all unrestricted schedules and include installed capacity, interval duration, and known availability. Additional bounds such as \(a_{jt}\le N\bar P_j\Delta_t\) are valid with a universal per-bus grid-power cap. Route restrictions or incumbent availability are insufficient. Charging/withdrawal ordering inside epochs may be relaxed by this stock model; endpoint feasibility remains only necessary.

## Interval, prefix and suffix deductions

Define \(Q_{ab}=\sum_{t=a+1}^bq_t\), \(D_{ab}=\sum_{t=a+1}^bd_t\). Telescoping and nonnegative additional withdrawal give
\[
Q_{ab}\ge D_{ab}+L_b-U_a\qquad(0\le a<b\le T).
\]
For internal intervals the basic version is \(Q_{ab}\ge D_{ab}-NU\): compulsory demand exceeding available aggregate storage must be charged inside that interval. Prefix bounds use the actual initial-stock upper bound, \(Q_{0b}\ge D_{0b}+L_b-U_0\); suffix bounds use the terminal lower bound, \(Q_{aT}\ge D_{aT}+L_T-U_a\). Clamp negative lower bounds to zero when purchases are nonnegative.

If a valid \(\bar H_{ab}\) exists, the complementary upper bound is
\[
Q_{ab}\le D_{ab}+\bar H_{ab}+U_b-L_a.
\]
Nonnegativity of deadhead alone cannot prove this upper bound: extra charge may pay for extra deadhead.

Known opportunity envelopes \(Q_{ab}\le\bar Q_{ab}\) strengthen endpoint bounds without a fleet solve:
\[
U_a\leftarrow\min\{U_a,U_0+\bar Q_{0a}-D_{0a}\},\quad
L_b\leftarrow\max\{L_b,L_T+D_{bT}-\bar Q_{bT}\}.
\]
Apply these tightened endpoints in the interval inequalities. A contradiction \(L_t>U_t\) excludes that fleet size under the assumptions. These cuts are consequences of the retained stock system, not stronger than that system itself.

Free initial charge matters: with \(s_0\le NU\) and no replenishment, total charging need only satisfy \(Q_{0T}\ge D_{0T}-NU\); service demand is not purchased-energy equality. If terminal replenishment requires \(s_T\ge s_0\), then \(Q_{0T}\ge D_{0T}\), even when initial charge is free. A suffix additionally obeys \(Q_{aT}\ge D_{aT}+s_0-U_a\); retain \(s_0\) to avoid weakening this coupling prematurely. Full initial/terminal batteries set both endpoint stocks to \(NU\).

## Occupancy and charging opportunity

Suppose mandatory trips occupy \(m(\tau)\) buses at physical time \(\tau\), charging is impossible during service, and each bus draws at most universal grid power \(P>0\). Then \(N\ge\sup_\tau m(\tau)\), and for any aligned interval \(I\),
\[
E_I\le P\left(N|I|-\int_I m(\tau)d\tau\right),\qquad
E_I\le\int_I C_{\rm station}(\tau)d\tau.
\]
Ignoring deadheading increases charging opportunity and is a valid relaxation. Partitioning at occupancy/capacity changes and imposing both caps on each segment can tighten the coarse interval bounds. All included grid load must be attributable to this fleet. Mandatory service energy and occupied bus time are different quantities.

For horizon length \(H>0\), mandatory occupied bus time \(M\), efficiency upper bound \(\eta_{\max}>0\), and total compulsory withdrawal \(D\), replenishment implies the necessary bound
\[
N\ge\frac{M+D/(\eta_{\max}P)}{H}.
\]
Without replenishment and with free initial stock at most \(NU\), instead
\(N\ge(D+\eta_{\max}PM)/(U+\eta_{\max}PH)\).
Installed capacity also requires \(\eta_{\max}\int C_{\rm station}\ge D\) under replenishment. Shared charging windows require restricting both duration and occupied-time integration to those windows. These are necessary energetic/resource bounds, not sufficiency claims.

## Endogenous fleet size and cost

Retain \(N_{\min}\le N\le N_{\max}\) as a continuous variable in an outer model; every physically integer fleet remains included. Stock bounds, occupancy caps, station-energy allocation and balances are linear when their stated envelopes are affine. Piecewise caps can be represented by multiple affine upper inequalities. If intrinsic cost contains \(fN\), \(f\ge0\), and **all other intrinsic terms are nonnegative**, retain \(c\ge fN\). Credits, negative intrinsic terms or a differently defined fleet charge invalidate that floor.

For cached certificates add \(c+p_k^\top e\ge\ell_k\). Project this convex outer model to cost/load space, or keep its auxiliary variables when evaluating the joint bound. This preserves the useful coupling between load, fleet size and cost. Safely eliminating fleet size using \(N_{\max}\) weakens upper stock/opportunity bounds and corresponding interval lower bounds; use independently valid endpoint bounds. Never substitute an incumbent fleet count. A projection also needs a proven finite \(N_{\max}\); otherwise compactness cannot be assumed.

## Two exact hand examples

**Strict certificate improvement.** One bus has usable capacity one, zero initial stock, two charging epochs with grid caps one and efficiency one, followed by compulsory service withdrawal one. The two allowed complete schedules have \((e,c)=((1,0),0)\) and \(((0,1),1)\). Cached exact values are \(V((0,0))=0\), \(V((2,0))=1\). At query \(p=(1,1)\), the hardware-box joint bound is
\[
\min_{[0,1]^2}\max\{e_1+e_2,1-e_1+e_2\}=1/2,
\]
attained at \((1/2,0)\). The mandatory-energy facet \(e_1+e_2\ge1\) raises it to one: the first expression is at least one, and \((1,0)\) attains one. Actual \(V(p)=1\). This is a structural tightening of the joint certificate, proved without computation.

**Aggregate feasibility is insufficient.** Two buses each have usable capacity one and start full. Epoch one contains an indivisible trip withdrawing 1.5 from its assigned bus, with charging prohibited. Epoch two allows grid charging 1.5 at efficiency one, installed capacity two, and per-bus epoch cap one. Aggregate stocks \((s_0,s_1,s_2)=(2,0.5,2)\) satisfy balances, reserve/full bounds, occupancy caps, interval cuts and replenishment. Yet no bus can execute the trip: its individual usable battery is only one. Aggregate energy cannot establish individual route feasibility.

## Interpretation

The structural stock/opportunity constraints may already be implied by projection of a correctly formulated full continuous fleet relaxation. An exact projection has the same relaxation value; retaining only a subset of those implied constraints generally weakens it. Their potential saving is cheap construction and reuse, rather than strengthening that full LP. **Integer-oracle cache cuts are a separate source of strength:** a globally valid \(\ell_k\) can exceed the continuous pricing optimum, so \(c+p_k^\top e\ge\ell_k\) can exclude full-LP points. The cache-enriched model therefore has no automatic dominance ordering against the unaugmented full LP. Whether compact stock/opportunity cuts materially improve time to certified economic accuracy is a prospective question requiring matched total-cost comparisons.
