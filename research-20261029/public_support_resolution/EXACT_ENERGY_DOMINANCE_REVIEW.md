# Independent analytical review: exact energy canonical dominance

Reviewed EXACT_ENERGY_DOMINANCE_LEMMA.md without instance values, numerical tools, imports, execution, hashes or source edits. The fixture-ID correction is separate: synthetic fixtures now use genuine canonical movement-ID patterns while retaining explicit synthetic case identities.

**Verdict: the lemma supplies sound sufficient conditions for its explicitly defined larger modeled opportunity set. It does not establish that the public stored coefficients satisfy them.** No counterexample was found under the full stated conditions. The retained caveats about exact wait laws, discounted alternatives and charging labels are essential rather than editorial.

## Energy comparisons

For a no-depot gap, the exact additive wait law gives energy ρT+Σ(q−ρτ). Non-depot w triangles reduce the sum to w_ij, and the separately required stored canonical-total comparison then gives no greater consumption. Directed time triangles ensure direct travel fits in the same service gap. Nonnegative consumption in both old and canonical no-charge evolutions makes endpoint inventory sufficient: the canonical SOC need not dominate pointwise, only remain above reserve throughout and have enough inventory for the unchanged next service.

For a depot-visiting gap, the q triangles and nonnegative waits separately dominate the inbound prefix and outbound suffix. These are the correct weights: applying w to depot parked time would incorrectly charge auxiliary energy where the model assigns zero draw. Earliest inbound/latest outbound containment preserves all original charging clocks inside the canonical gap. Prefix/suffix and direct-mode comparisons must cover every applicable stored component and service-boundary alternative; checking only primitive triangles does not cover discounted stored waits automatically.

Zero diagonal and ALL ordered non-depot w triples, including repeated endpoints, exclude negative w cycles by successive triangle reduction. Clarify “i,j,k different from d” as “each index is non-depot, repetitions allowed,” to avoid a reading that only pairwise-distinct triples are checked. In particular repeated-endpoint inequalities control two-arc cycles.

## Charge curtailment and full inventory

At the first original depot arrival, the canonical bus has consumed no more energy and starts charging from inventory no smaller. With no parked draw, curtailment at capacity produces capacity-clipped cumulative original charging. The old bus's additional excursions only subtract energy, so its feasible inventory never exceeds that clipped canonical inventory. Outbound consumption is no larger, preserving the next service's feasibility. Applying this induction across unchanged nonnegative service consumption and gaps proves the stated replacement. During terminal replenishment there is no later compulsory consumption after the final return; the original schedule's final full inventory forces the clipped canonical inventory to reach the same full capacity, not merely remain above reserve. Each grid-period purchase is only curtailed at its original time, so shared-connector feasibility and componentwise load dominance are preserved.

For standalone clarity, retain the public model's nonnegative mandatory service consumption and no in-service charging/recovery assumptions explicitly. With regenerative service gains, a larger incoming SOC could create a capacity violation and this simple monotone induction would need another argument. Likewise no minimum charging amounts, taper, positive depot draw, fixed session commitments or charging-label restrictions may be silently introduced. The lemma already states unit efficiency for this construction; it is not an efficiency-generalization claim.

## Inclusion and waits: no shortcut

A lower stored canonical coefficient may be incompatible with the primitive/linear-wait law. The proposed alternatives address this correctly: prove compatibility, or retain old canonical gaps as separate WHOLE-gap options, leave an old canonical gap unchanged, and replace only primitive-walk gap options. Allowing arbitrary discounted subcomponents to be spliced into primitive walks would invalidate the lower-bound argument. A “canonical total” inequality alone is not proof that the old and new laws coincide.

The global-wait-envelope variant is also sound: replacing exact equality by W(t)≥ρ_lower t gives the same required lower bound for every admitted gap, provided prefix/suffix waits remain nonnegative and the canonical-total comparison uses that same envelope coefficient. A finite set of rounded waits cannot establish this bound for arbitrary real durations or subdivisions. Underflow and separately rounded sums are genuine seams. No tolerance, coefficient replacement or sampled-duration qualification can close them.

## Scope and recommendation

Canonical inclusion plus the constructed domination proves equal physical infima for coordinatewise nondecreasing supply objectives. Replacing every finite-mixture component proves the hull infimum statement. It proves neither equality of complete load projections nor all zero-price response sets. Negative prices, different access locations, hidden tasks, nonadditive travel/waits, time-varying arcs or empirical joint-route claims remain outside scope.

The note is suitable as a prospective sufficient-condition lemma after the two explicit clarity points above. Its finite q/w/canonical-total prerequisites, complete primitive table, exact arbitrary-wait law/envelope and common terminal-access policy must be separately admitted. Current metric PASS and energy-formula provenance do not supply them. If any remains unavailable or false, the existing finite declared-mode certificate stays the appropriate conclusion.
