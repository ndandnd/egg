# Charging-route relaxation: independent mathematical checks

2 October 2026. Algebra and hand counterexamples only, based on the specified review notes. No additional source or implementation verification, data access, optimization, training, or cluster work. These are standard relaxation and dual-bound conditions, not novel results.

## Physical mapping and objective direction

For every feasible complete fleet x, establish a route-master representation y satisfying all retained constraints and
\[
c_Y(y)+p^\top e_Y(y)\le c(x)+p^\top e(x).
\]
Only then does minimizing over the full route relaxation lower-bound full-fleet pricing V(p). Preserving load and not increasing intrinsic cost suffices at every price. Otherwise specify the permitted finite price domain and prove the inequality there. Finiteness of each price alone is insufficient; a bounded domain permits an explicit error allowance, but does not automatically justify rounding.

**Discretization:** SOC feasibility optimism need not imply economic optimism. Deleting one purchased energy unit at price −10 raises cost from −10 to zero. Moving a unit between intervals priced (0,10) raises cost from zero to 10. Time/SOC rounding must preserve objective direction, not merely extend battery feasibility.

**Shared capacities:** Dropping a charger constraint is a valid weakening. Rounding route occupancy upward or capacity downward can instead exclude physical fleets. Preserve actual simultaneous resource coefficients or prove their optimistic direction for each upper-capacity row. Use consistent additive grid-energy accounting, including losses and charging timing.

**Route counts:** Every physical fleet must satisfy retained depot/type/cardinality rows after mapping. A bound by trip count needs every counted vehicle to serve a trip. Idle charging vehicles can defeat that inference, especially under negative prices; terminal and charging permissions matter. A finite route-mass bound must follow from the physical domain or a proved equivalent representation.

**Dominance:** Earlier arrival or greater SOC alone does not establish dominance with signed prices and shared occupancy. Battery headroom may permit profitable negative-price charging. Dominance must preserve feasible continuations with no higher total cost and compatible master-resource contributions.

## Incomplete columns and corrected dual bounds

A restricted minimization master gives an upper bound on the full route LP, not automatically a lower bound on V(p). For master Ay=b, Gy≤h, y≥0 at a fixed price, let c denote the vector of route costs including the energy bill; take equality dual π free and capacity dual μ≤0. Let D=πᵀb+μᵀh and reduced costs r=c−Aᵀπ−Gᵀμ. For a feasible representation,
\[
c^\top y=\pi^\top b+\mu^\top Gy+r^\top y
\ge D+\rho\sum_r y_r
\ge D+K\min(0,\rho),
\]
provided every unrestricted route satisfies r_r≥ρ and route mass is at most justified K. Other row senses require their corresponding dual signs. Heuristic or pruned-network pricing cannot certify global ρ. Without finite mass, negative reduced costs admit no finite correction of this form.

Even exact route pricing does not identify the complete-fleet hull: three trips, pair routes costing one and singleton routes costing one admit half of each pair for fractional cost 1.5, while an integral fleet costs at least two. A valid route relaxation remains distinct from complete-fleet convexification.

## Protocol review and corrections

The same independent reviewer checked the final protocol's explicit mass-row dual and confirmed its certificate and 18+2 / 36+4 CPUh arithmetic. Parent and reviewer identified a measurement floor: if the comparator has certified the optimum by the final cap, its final bound error is zero. The protocol now fixes an earlier comparison checkpoint, permits a reference established later within the budget, and retains zero-error ties. The small cohort is registered before outcomes; missing references make its promotion gate inconclusive rather than allowing selection of a favorable certified subset. Any numerical reference enclosure propagates into the comparison. Parent also clarified that the reduced-cost floor covers the entire optimistic route universe, including artificial routes.
