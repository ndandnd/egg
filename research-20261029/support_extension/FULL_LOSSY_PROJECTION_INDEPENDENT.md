# Independent complete common-loss projection review

**PASS under the explicitly stated ideal cycling assumptions.** The proposed extended polygon describes the complete aggregate projection for a fixed matching, not only its efficient part. The minimum-R matching at each cardinality consequently reproduces every other matching's aggregate point at the same cost. Economic monotonicity is unnecessary for optimization over this COMPLETE set. This is a source-only analytical result: no data, numerical execution, imports, tests, hashes or other agent's candidate were used.

## Precise model required

There is at least one used service-assigned bus, common battery capacity B>0, zero reserve, common efficiencies0<alpha,delta<=1, common early and terminal windows of unit duration, and fixed mandatory A/B services as in the current common-loss model. Every bus is present for the whole early window. Only early actions may export; terminal replenishment is charge-only and restores each bus to full. Early shared power is K and terminal shared power H, on the grid side; each bus can accept the full corresponding charge/export power. One connector may serve only one bus/direction at a time. There is no taper, switching delay/cost, minimum session or positive lower bound on action duration. Any finite number of early direction changes is permitted. Consumption is nonnegative and no action occurs inside a service. All operating cost is determined by the counted fleet, not gross throughput, cycling or session count.

For a fixed matching, let x_v be each bus's net battery exchange in the early window. Its endpoint constraints are the boxes

- paired: `[a_i+b_j−B,a_i]`;
- A-only: `[a_i−B,a_i]`;
- B-only: `[b_j−B,0]`.

Each upper endpoint is nonnegative. Write l_v,u_v for these bounds, R=sum(l_v)_+, T=sum l_v=S−NB, and P=sum u_v=sum a_i. These box properties, not arbitrary boxes with negative upper endpoints, are used below.

## Exact fixed-matching statement

Aggregate early grid purchases C and exports X are attainable, with total terminal purchase L, if and only if

`C>=R/alpha`, `X>=0`, `T<=Q=alpha C−X/delta<=P`,

`C+X<=K`, `L=(S−Q)/alpha`, `0<=L<=H`.

The early net load is E=C−X. Every point of this closed bounded extended polygon has a physical schedule with finitely many early actions. No limit of infinitely fast chatter is required.

### Necessity

For each bus, x_v=alpha C_v−X_v/delta lies in its box. If l_v>0, then C_v>=l_v/alpha regardless of how often the bus changes direction. Summing gives C>=R/alpha. Summing boxes gives T<=Q<=P. Shared serial grid power gives total gross energy C+X<=K. Initial and final full inventory and fixed service consumption give alpha L=S−Q. Terminal charge-only access gives0<=L<=H. These statements do not assume one direction per bus.

### A one-direction baseline for any Q

For Q in[T,P], the least possible total positive battery exchange is

`A_+(Q)=max(R,Q)`.

If Q>=R, hold mandatory-positive coordinates at their lower endpoints, put all other coordinates initially at0, and distribute additional positive exchange up to the independent upper endpoints. Their aggregate positive interval is[R,P]. If Q<R, hold positive-lower-bound coordinates at their lower endpoints and distribute negative exchange over the other coordinates. Their total available negative magnitude is R−T, exactly enough whenever Q>=T. Thus the displayed lower bound is both necessary and attained.

The corresponding one-direction grid totals are

`C0=max(R,Q)/alpha`, `X0=delta(max(R,Q)−Q)`.

Given any proposed C,X satisfying the polygon, Q<=alpha C implies C>=Q/alpha, while the mandatory condition gives C>=R/alpha. Hence h=C−C0>=0. Conservation gives

`X−X0=alpha delta h`.

The residual totals are therefore precisely a battery-neutral cycle: h grid units purchased and alpha delta h grid units exported.

### Finite cycle construction, including empty/full inventory

Choose any used bus at its feasible early starting inventory s in[0,B]. Before its baseline one-direction action, perform neutral cycles on that bus returning it to s each time. A cycle of battery amplitude z purchases z/alpha and exports delta z. If s<=B/2, charge first and then discharge; if s>B/2, discharge first and then charge. Every amplitude0<=z<=B/2 is safe in the chosen direction. This includes s=0 and s=B without a headroom or inventory exception.

Split the required battery amplitude alpha h into finitely many pieces at most B/2. For h>0, at most ceil(2alpha h/B) such cycles suffice; for h=0 no cycle is needed. Gross budget K makes h finite. Append the prescribed baseline actions for all buses. Every cycle and baseline action is monotone between valid inventories, and the baseline endpoint boxes ensure feasibility before and after B and throughout the noncharging services.

Serialize every charge/export action at grid power K when K>0. Their combined duration is exactly(C+X)/K<=1, so the finite action list fits the common window; no simultaneous purchase/export is needed. If K=0, the polygon forces C=X=0 and no early action is used. This is why finite action count, zero switching delay and unrestricted direction changes matter.

After B, bus v needs battery refill equal to its service consumption minus x_v, a quantity in[0,B] by its endpoint box. Charge it monotonically at the terminal connector, requiring that amount divided by alpha on the grid. Total grid duration is L/H<=1 when H>0. If H=0, L=0 requires no action. This proves full physical attainment and completes sufficiency.

## Exact cardinality reduction and economic scope

At a fixed cardinality m, N,S,T,P and operating cost c=fN are independent of matching. The ONLY matching-dependent coefficient in the extended polygon is the lower bound C>=R/alpha. A matching attaining r_m therefore has a polygon containing that of every other matching of the same size. Since it is itself physical, the union over all matchings at that cardinality equals its polygon exactly. In particular it reproduces the SAME C,X,E,L,c, not merely a point with smaller coordinates.

Take the linear image `(E,L,c)=(C−X,(S−alpha C+X/delta)/alpha,f(2n−m))` of each nonempty r_m polygon and the finite union over m=0,...,nu. This is the complete joint projection for the declared service-assigned model, including lossy cycles. Its convex hull is the exact complete-plan convexified projection. Arbitrary objectives defined on this projection—including nonmonotone convex supply or negative posted rates—may be optimized on it without a dominance-based deletion. This does not revive the failed continuous-cardinality shortcut: the discrete union must still be convexified exactly, e.g. by its finite polygon vertices or a disaggregated mixture formulation.

For rational physical parameters the extended polygons and their images are rational. No new numerical implementation qualification, runtime claim or public-timetable result is established here. Paid idles, if separately included, require an explicit total-fleet interpretation; the fixed-matching statement itself does not need them.

## Lossless degeneracy

When alpha delta=1 under the stated efficiency range, alpha=delta=1. Then Q=E and L=S−E, while neutral cycles change C and X equally and disappear from the projected loads. Existence of some feasible gross allocation is equivalent to

`T<=E<=P`, `max(E,2R−E)<=K`, `0<=S−E<=H`.

This reduces to the familiar closed lossless interval. The extended polygon remains valid even though its(E,L) image loses dimension; no division by kappa is justified in this limit. For positive losses, retaining C,X likewise avoids an unnecessary inversion or a degeneracy seam.

## Boundaries that must remain explicit

The claim can fail if cycles are forbidden, directions may switch only a fixed small number of times, switching/session times are positive, individual power acceptance is below the connector without additional scheduling constraints, availability windows differ, throughput/cycling adds operating costs, exports are unavailable, or terminal replenishment has different access rights. B=0 or an empty fleet cannot supply the one-bus cycling construction. Different efficiencies by bus can make R,T,P insufficient aggregate statistics. Multiple market intervals within the nominal early window require corresponding time-resolved coordinates; the present aggregate proof does not preserve an arbitrary intrawindow load profile. These are model assumptions, not harmless implementation details.

The previous efficient-frontier formulas remain correct for monotone economics, but they are not the whole projection. The complete polygon is a separate exact statement that includes the cycles those formulas deliberately removed. It removes the monotonicity requirement only when the full extended polygons are retained, not when the smaller efficient set Z is used for a nonmonotone objective.

## Addendum: identical paid idles under the total2n cap

PASS: with identical idle buses admitted under the TOTAL fleet cap2n, the complete joint projection remains EXACTLY unchanged. If the service assignment has matching size m and q idles, then N=2n−m+q<=2n implies q<=m. An idle bus starts full and has box[-B,0]; it adds zero to R and P and adds−B to T. Thus the original fleet still has T=S−NB and precisely the full polygon proved above.

Delete any q matching edges and assign each released service separately. The resulting allowed partial matching has size m−q and no idle buses, hence the same N and fee. Service totals S and P are unchanged, T remains S−NB, and the new R cannot increase. Its exact full polygon therefore contains the idle fleet's polygon at the SAME C,X,Q,E,L,c. Reverse inclusion holds because every all-assigned fleet was already admitted in the enlarged model. No monotone-objective assumption or domination step is needed.

This uses identical capacity/efficiencies/fee/power acceptance, full common early and terminal availability, the unrestricted finite neutral-cycle construction, and zero transition consumption/cost. Released A-only/B-only buses have the common-window access required by the box model; changing their initial early inventories does not impair finite cycling, which was proved for every inventory in[0,B]. Merely changing the count while granting an idle bus special access or acceptance would not justify the claim. Without the total cap q<=m need not hold. With positive per-matching transition consumption, deleting edges can change S, so this exact argument does not extend verbatim.
