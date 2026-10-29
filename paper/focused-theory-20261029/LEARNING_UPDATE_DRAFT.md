# Learning update — consolidated changes for the existing guide/deck

Draft for parent integration after the public tree phase closes. The public **global** support result is pending. This note does not inspect that running attempt, replace the full self-study guide, or edit the existing22-slide learning deck. It uses the existing support-extension guide, current readable two-batch/V2G theory and the completed price-witness readout; no computation or literature search was performed.

## The conceptual correction: loads can be convex while load–cost pairs are not

The obstruction need not be a missing charging load. In the fixed shared-connector two-batch model, every early total E between the resource limits L and U is physically attainable: use separate buses if necessary and distribute their continuous charging. The late total is S−E. So the energy-only set is an ordinary interval.

But different early totals can require different bus counts. A low early purchase may need more buses; pairing services on fewer buses may require extra energy before the second batch. The cheapest operating cost therefore drops in steps as E passes assignment thresholds. Keeping only the load interval erases those cost labels.

The hull fills lines between complete plans' **load and operating-cost pairs**. At an intermediate E, that E may already be physical, but the interpolated operating cost may be cheaper than any bus assignment can deliver there. This is why continuous charging does not by itself remove the obstruction. It is not necessary to claim that the mean energy load cannot be dispatched; the relevant missing object is the joint load–cost pair.

## What the fixed shared-connector result now says

This result uses one early connector of power K and one terminal connector of power H, not n scaled connectors. Every bus starts and ends full. Services occur in two simultaneous batches; permitted transitions have zero time/energy/cost and every service keeps a standalone option.

For each allowed matching size m, r_m is the least early recharge forced by sharing buses. The physical branch is an early-load interval starting at max(L,r_m), with fee f(2n−m), where L=max(0,S−H) and U=min(sum A,K). Cardinalities whose threshold exceeds U are infeasible; they are not clipped into invented schedules. A declared allowed successor graph may be sparse. The sorted-smallest/opposite-pairing shortcut applies only when all cross-pairs are allowed.

For positive fee and strictly convex supply along the fixed-total-energy line, find the hull's best E. A physical plan attains it exactly when it lies at the clipped left endpoint, a retained physical assignment threshold, or the final flat operating-cost segment. A point strictly between adjacent retained thresholds gives a positive planning gap. Retain intermediate physical thresholds even if the geometric hull merges their collinear edges. Zero fee needs separate handling: its gap is zero whenever feasible.

The separate14-case exact qualification checked the complete-crossmatching implementation, including the physically attained collinear E=20 and clipped-boundary E=5 cases. It does not numerically qualify every sparse graph. The older eight-case study concerns a different, adequate-resource policy; keep the two denominators separate. Here K means **early** power and H terminal power; the older connector/fee example used K for terminal power.

## V2G changes both physics and settlement

The new V2G section is analytical, not an implemented V2G experiment. It assumes lossless bidirectional early charging, uniform acceptance, full terminal replenishment, and the same posted rate for purchases and exports in an interval. Supply must be defined on every admitted signed net load, or through an explicitly declared background-demand model. Asymmetric buy/sell tariffs and losses are different models.

Connector time depends on **gross** energy. Buying1 and exporting1 has net load0 but consumes2 units of connector throughput. Checking only the absolute net total would create fictitious charging capacity.

V2G can leave the obstruction intact. In the earlier two-by-two example with K=15 and H=49, the inventory/throughput thresholds remain0,0,9. More individual battery actions do not change the joint frontier, so the previous positive gap persists.

It can also restore support. In the new three-by-three illustration, one assigned bus buys1 early while another exports1. Net early energy is0, gross throughput is2, and every battery is refilled terminally. Under that example's stated supply cost, the charge-only gap1/4 disappears and the supported physical value is67/5. The mechanism is redistribution of *when assigned inventories are available*, not free initial energy or cancellation of connector time.

Paid idle buses require a stated limit. With at most2n buses total, their entire load–cost projection is already represented by deleting matching edges and using the corresponding standalone service buses. For the examples with H=S, even uncapped fleets above2n are more expensive at loads that standalone buses can already realize. This latter dominance is **not** general when H>S: extra idle inventory can permit useful negative early net load. Do not teach that idle buses are always irrelevant.

## What the public witness proves, and what is still pending

The completed new price-witness package gives a strictly admitted feasible alternative whose bill is cheaper at the protected incumbent's fixed own prices. Its original quadratic planning cost is higher. These statements are compatible: supply cost and a bill at a fixed tariff are different objectives.

The positive exact regret proves that **this incumbent is unsupported at its own marginal prices**. Its charging optimum is known conditional on its routes; neither that fact nor a numerical global OPTIMAL label identifies the exact globally optimal physical fleet. The newly admitted alternative is fixed-route optimal for a separate linear-price objective, not an unrestricted fleet response or quadratic planner optimum.

An independently checked mixture of the two admitted plans supplies a hull upper below the protected physical objective. That strengthens the evidence, but still does not prove that global D exceeds global CH. A separately checked physical lower strictly above this hull upper would settle the positive sign. The current public tree attempt is intended to provide that lower; its global conclusion remains **PENDING** in this draft. Do not infer its outcome from the incumbent regret, native status, or a partial tree.

## Proposed six-slide delta

1. **A convex load interval can hide a nonconvex cost frontier.** Show one interval of possible charging totals, then add the bus-count cost steps. Mark one physically attainable load whose hull operating-cost label is unattainable. Takeaway: keep `(load, operating cost)` together.
2. **One shared connector: the exact classification.** Show the physical staircase, hull segments and clipped L/U. Mark supported endpoint/threshold/flat locations and unsupported open intervals. Note fixed resources, allowed graph and the separate14-case complete-graph qualification.
3. **V2G: net zero still uses the connector.** Draw purchase+1/export−1, net0/gross2, then terminal refill. State equal-rate settlement and the signed supply domain explicitly.
4. **V2G can preserve failure or remove it.** Contrast the unchanged0,0,9 thresholds with the three-bus restoration example. Add a short paid-idle-bus note: unchanged under the2n cap; uncapped dominance here relies on H=S.
5. **Public incumbent test versus global support.** Show three boxes: admitted fixed-route incumbent; cheaper feasible response at fixed prices; feasible two-plan hull upper. Leave the separate global physical-lower/complete-tree box visibly PENDING until its exact audit closes.
6. **What improved—and what did not become an ML result.** Separate analytical theorems, finite exact implementation checks and public certificates. Matching, convex QP/LP and certificate construction are classical methods. These updates establish no neural advantage, operational prevalence or new learning benchmark.

The existing learning pilot's classical comparisons and limitations still stand. Larger capacity helped within that pilot but did not beat its best fitted classical control; the old GNN diagnosis remains a different question. A stronger economic model or exact certificate is not evidence of an ML improvement. Any later learning claim still needs a valuable decision mechanism, strong controls and complete paid end-to-end accounting.

Sources: `research-20261029/support_extension/GUIDE.md`; `paper/focused-theory-20261029/heterogeneous.tex`; `paper/focused-theory-20261029/v2g.tex`; `research-20261029/public_price_witness/RESULTS.md`. No deck file or earlier guide was modified.
