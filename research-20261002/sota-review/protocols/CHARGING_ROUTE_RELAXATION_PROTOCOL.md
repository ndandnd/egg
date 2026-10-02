# Prospective charging-route relaxation protocol

2 October 2026. **Design only, not implementation or a frozen launch protocol.** No execution authorized. Implements rank 5 and Section 3.4 of [SOTA_REVIEW.md](../SOTA_REVIEW.md), with the verified EV2/EV3/EV1 algorithmic precedents in [EV_PRICING_AND_HULL.md](../notes/EV_PRICING_AND_HULL.md) and the conservative/optimistic-network distinction in [BOUND_DOMAIN_COMPARISON.md](../notes/BOUND_DOMAIN_COMPARISON.md). The latter identifies the inspected de Vos–van Lieshout–Dollevoet author version and final-publication access limits. No code, data or model access, protected-file inspection, cluster work, solves, training or new web search accompanies this design.

## Original-to-relaxation obligation

Let X denote the unchanged feasible **complete coupled fleets** and
\[
V(p)=\inf_{x\in X}\{c(x)+p^\top e(x)\}.
\]
Define a proposed route relaxation Y and prove, for every x and allowed price p, a representation y in Y satisfying
\[
c_Y(y)+p^\top e_Y(y)\le c(x)+p^\top e(x).
\]
Then \(\inf_Y(c_Y+p^\top e_Y)\le V(p)\). This is an unresolved model-mapping obligation, not an established EGG result. Prefer preserving e exactly and never increasing intrinsic cost; that establishes the direction for every signed price. If a discretization changes energy/timing, prove the inequality on the entire registered price domain, possibly using a price-dependent mapping.

The mapping ledger must cover all trips/deadheads, depot starts/ends, bus selection and multiplicity, initial/terminal energy, reserve, charge/discharge efficiency, regeneration, continuous windows, rate limits and shared resources. Decompose each physical fleet into bus duties, including admissible empty/idle duties. Each mapped route contributes its trip indicators, intrinsic cost, grid-load vector and station/time resource footprint. Show coverage, resource and fleet constraints and cost summation explicitly; nonseparable costs need a justified lower-cost representation.

## Route master and two network roles

For columns r containing a duty **and its charging trajectory**, let \(a_r\) encode coverage/depot requirements and \(g_r\) encode shared charger occupancy/power. The proposed master is
\[
\min_{y\ge0}\sum_r d_r(p)y_r,
\quad Ay=b,\ Gy\le h,\ \sum_r y_r\le K,
\qquad d_r(p)=c_r+p^\top e_r.
\]
Register signs and meanings of each row. Physical fleet mapping assigns integer multiplicities; the LP permits fractions. Shared occupancy and site power cannot be replaced by independent per-route access if claiming an exact representation. Removing or weakening coupling can yield an explicitly looser bound, provided mapped fleets still fit. Rounding occupancy upward or capacity downward may exclude them. Import/export power and plug occupancy require distinct coefficients when net energy masks physical use.

Prove a finite uniform upper bound K on route mass for every mapped fleet; retain fleet/depot multiplicities. K cannot automatically equal trip count: that requires every counted bus to serve a trip, while idle charging buses may matter under negative prices. Extra route cycles or zero-duration charging must not allow unbounded purchases or negative-cost cycling. Without boundedness and an applicable K, the correction below is unavailable.

Keep two network contracts separate. A **conservative candidate network** removes choices or rounds for safe duty construction; only jointly completed, replay-valid fleets become physical candidates. Its minimization bound cannot certify V. An **optimistic bounding network** represents every original duty/fleet without increasing the price objective, even if its artificial routes are physically unrealizable. Do not submit those routes as executable fleet columns. An integral route selection still requires shared-capacity completion and independent fleet replay.

## Signed prices, resources and dominance

Deleting one purchased unit at p=-10 changes its objective contribution from -10 to 0 and destroys the desired direction. Moving a unit between intervals with prices (0,10) changes 0 to 10 despite preserved energy. SOC-feasibility rounding alone therefore cannot prove an objective bound. Freeze price coordinates, units and allowable domain; keep charging interval identity or derive outward lower cost envelopes valid throughout that domain.

Forward extensions, backward bounds and dominance must include time, SOC, economic cost and shared-resource dual contributions. More SOC can remove profitable charging headroom at negative prices; a cheaper label with a worse station footprint may have costlier extensions. Require a proof of compatible resources and noncostlier feasible extensions before dropping a label. Heuristic sparsification/dominance supplies candidates, not global absence certificates. Label-count and memory caps must return an incomplete result unless a separate valid lower-bound argument survives truncation.

## Incomplete column generation: admissible certificate

An incomplete restricted-master minimization value is an **upper** bound on the full route LP, not a fleet-pricing lower certificate. A learned/heuristic route incumbent similarly upper-bounds the minimum reduced cost.

For any registered master multipliers \(\pi\) free, \(\mu\le0\), \(\beta\le0\), define
\[
z=b^\top\pi+h^\top\mu+K\beta,\qquad
q_r=d_r-a_r^\top\pi-g_r^\top\mu-\beta.
\]
If a certified global floor \(\rho\le q_r\) holds for **every** route in the full optimistic bounding universe, including artificial routes, then
\[
\ell_R=z+K\min(0,\rho)\le\min_Y d^\top y\le V(p).
\]
The proof uses the coverage identity, signed capacity inequalities, nonnegative route weights and total mass at most K. RMP dual optimality is unnecessary; sign/domain validity and a globally valid pricing floor are essential. Per-depot corrections require corresponding proved mass bounds. A pruned-network minimum or truncated-label incumbent is not rho; a valid global pricing lower bound remains usable under timeout.

Recompute reduced costs after any multiplier projection. Receipts must record master/price/route-domain hashes, multipliers/sign checks, K proof, pricing status and floor, and outward numerical allowances. Enclose z and rho downward and the negative correction conservatively; residuals cannot be ignored or hidden in a restricted-MIP gap. If the floor, mapping or numerical enclosure is unverified, issue **no global certificate**. For optional hull use, subtract an upper enclosure of the applicable supply conjugate; that arithmetic is outside this pricing-only comparison.

## Route LP versus complete-fleet hull

Convexifying individual routes and then imposing shared fleet constraints can be weaker than convexifying already coupled complete fleets. Hand example: three trips, all pair-covering routes and singleton routes costing one each. Half of each pair route covers all trips for cost 1.5; any integral complete cover needs cost 2. The complete-fleet hull preserves that linear minimum of 2. Thus an exact route LP does not establish complete-fleet CH values/prices; equality needs an additional theorem.

## Adversarial proof/implementation matrix

These are prospective hand-constructed tests, not executed cases. Later enumerate complete toy fleets and routes independently where finite.

| Toy | Required check |
|---|---|
| Two buses, one shared plug/window | Every physical fleet maps; optimistic occupancy does not exclude it; candidate admission rejects collisions. |
| Fractional pair-cover example | Route LP=1.5, complete-fleet linear minimum=2; no hull-equality claim. |
| Positive price jump and negative purchase price | Time shifting/energy deletion cannot raise mapped cost. |
| Idle bus, regeneration/export, full replenishment | Correct multiplicities, K, signed load and boundary accounting. |
| Extra-SOC/charging-headroom labels | Dominance retains all cost/resource-relevant extensions. |
| Missing cheap column; interrupted pricing | RMP objective is rejected as a certificate; corrected bound stays below enumeration. |
| Tiny dual residual, sign/rounding perturbations | Outward receipt survives, or explicitly fails admission. |

## Paired fixed-price screen, resources and decision

Before launch freeze 12 permitted cases from distinct timetable groups: six small and six larger, each with three fixed price vectors, three paired seeds, and two methods (unchanged full-fleet MIP and route relaxation). Assign the small cohort by size before outcomes, never by which cases certify during screening. Prices cover variation and permitted signed values. No price adaptation, cross-method incumbents, new training or outer hull loop. Public cells are exploratory and cannot tune the network. Freeze solver/hardware, initialization, embedding, tolerances, stage caps, reference provenance and failure rules. Original-model verification and toy checks are prerequisites, not supplied by this document.

Choose one common allowance, **300 or 600 seconds**, before measurement. Arithmetic: \(12\times3\times3\times2\times300/3600=18\) solver CPUh, or **36 CPUh** at 600 seconds. Allow respectively 2 or 4 CPUh for engineering checks/preprocessing/replay/certificate overhead: **20–40 CPUh total**, a 40 CPUh ceiling. Charge construction, restricted masters, every pricing call, completion and verification inside matched end-to-end caps; failures/retries consume allocation. Timing must establish feasibility before launch; no extra reference solves or full branch-and-price campaign are included.

Log full-MIP root/best bounds and route corrected-bound trajectories, pricing/label counts, CPU/wall time, memory, failures and certificate provenance. Compare small-case normalized error \((V^*-\ell)/\max(1,|V^*|)\) at the fixed checkpoint \(0.2T\) of each common end-to-end cap T, including build time. V* may come from an eligible prior certificate, independent finite enumeration, or later full-MIP certification within that run's remaining budget. Reference acquisition/verification consumes the registered envelope; no extra reference solves are free. Carry reference enclosures into error comparisons and treat ambiguous thresholds as inconclusive. The small-case promotion gate requires valid references for all six registered groups and all their prices; otherwise it is inconclusive, with unresolved rows retained. Zero-error baseline ties remain in the cohort and cannot count as improvements. On larger cases freeze one common valid-bound target and censor unreached times. Group paired seeds/prices within timetables; never discard joint failures or count missing comparisons as wins.

Advance for **≥20% median normalized-error reduction at the fixed early checkpoint on the complete small cohort, or ≥25% time reduction to the same valid bound on larger cases**, including master overhead and with no certificate-integrity failure. Report the two gates separately: an unresolved small reference cannot count as success even if the larger-case gate succeeds independently. Freeze zero-error/censoring rules. Stop for wrong-model mapping, restrictive discretization, price-direction failure, label explosion, or bounds too weak to justify improving the existing oracle. No route architecture rewrite follows merely from successful route generation.
