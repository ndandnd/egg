# Positive setup time: conservative inner polygons and a boundary counterexample

**Conditional approximation PASS; unconditional convergence FALSE.** This is independent analytical reasoning only, without execution, data, imports, hashes, tests, other agents' candidates or numerical qualification. It does not assert an exact positive-setup-time hull.

## Model and a feasible inner polygon

Retain the complete common-loss model with nonempty service-assigned fleet, B>0, common efficiencies, full common availability and zero waiting/auxiliary draw. Let K_c,K_d>0 be the grid-side charge/export powers accepted by every bus. Every NONZERO early charge or export action now occupies the shared connector for a setup of duration tau>=0 followed by its energy-transfer time. Setup draws no energy, changes no inventory and has no separate monetary cost. Actions and setups cannot overlap. Terminal charging is unchanged. Fixed services, transitions, capacities and all other rights are unchanged; there are no additional minimum sessions or action-count restrictions.

For a fixed matching/cardinality let W_m be its exact ZERO-setup minimum-R polygon in(C,X), with occupancy

`ell(C,X)=C/K_c+X/K_d<=1`.

Its other four halfspaces are unchanged: C>=r_m/alpha, X>=0 and the two Q bounds. Define the fixed integer

`A_m=N_m+2 ceil(2 alpha K_c/B)`.

The conservative inner polygon is

`W_m^in(tau) = {z in W_m : ell(z)<=1−A_m tau}`.

Every point in it is feasible with setup time tau. The reviewed construction uses at most A_m nonzero early actions: finite neutral cycles on one bus plus at most one baseline action per bus. Insert a setup before each such action and execute energy transfers at their directional powers. Total early occupation is at most ell(z)+A_m tau<=1. Inventory is unchanged during setup; baseline and cyclic actions remain safe even at0/B. Terminal refill remains valid. This uses a bound on the constructed schedule, not an assertion that all schedules obey that action count.

If 1−A_m tau<0 the inner polygon is empty, even if a zero-action schedule might still be physically feasible. Thus it is deliberately conservative for large tau. For small tau the results below apply. With an a priori fleet cap2n, the common bound A=2n+2ceil(2alpha K_c/B) can replace each A_m. The formula with positive powers does not define a division at zero power: a zero-power direction must instead force its energy to zero, and no setup is needed for a zero action. The no-early-power special case C=X=0 is unchanged by early setup time.

Let P_tau denote the ACTUAL full joint projection with setup time tau, and P_0 the complete zero-setup projection. Map the inner polygons by the original affine load/cost maps and take their union P_tau^in. Then

`P_tau^in subseteq P_tau subseteq P_0`.

The right inclusion simply removes setup occupation; it does not use economic dominance. Common affine throughput wear, if retained, is included in the affine cost image and is unaffected by idle setup. An action-dependent monetary setup fee would require another coordinate/model and is not included.

## Sufficient slack for full projected-set convergence

Assume that for EVERY nonempty zero-setup cardinality polygon there exists a point z_m in that SAME polygon with strict occupancy slack

`sigma_m=1−ell(z_m)>0`.

Empty zero-setup layers require no slack representative; they remain empty under the positive-setup restriction. There are finitely many remaining layers. Set

`epsilon(tau)=max_m A_m tau/sigma_m`.

For sufficiently small tau, epsilon<=1. For any z in W_m, the complete convex interpolation

`z_tau=(1−epsilon)z+epsilon z_m`

still satisfies all four other halfspaces, and has occupancy at most1−epsilon sigma_m<=1−A_m tau. It lies in the conservative inner polygon and has a finite physical realization. This interpolation includes boundary vertices, point/segment degeneracies and changes of active constraints; no unproved local SOC perturbation or nondegenerate-face assumption is needed.

Let D_max be the largest diameter of the finitely many zero-setup AFFINE joint images, in any fixed norm. Then every point of P_0 is within epsilon D_max of P_tau^in. The reverse distance to P_0 is zero. Therefore

`d_H(P_tau^in,P_0)<=epsilon D_max`,

and the same bound holds for P_tau versus P_0, or their closures if desired. It also holds after taking complete-plan convex hulls: approximate each component in a finite mixture and use the same epsilon and the triangle inequality. This proves O(tau) set approximation for each fixed finite instance, with an explicit instance-dependent bound, not a uniform bound across instances as sigma_m tends to zero or the action count grows.

There is no claim that P_tau itself is a union of the simple five-halfspace polygons. The true positive-tau action/session constraints may create a more complicated set. The two inclusions and constructive approximation suffice.

## Value convergence: exact sufficient assumptions

For an arbitrary objective continuous on the common compact zero-setup joint domain, the set approximation and uniform continuity imply convergence of physical and hull INFIMUM values. This statement needs continuity; arbitrary discontinuous economic functions cannot be covered just by Hausdorff convergence. No positive-tau attainment theorem is needed to compare infima.

For the manuscript's convex supply objective J(u,c)=c+F(u), a direct convexity argument is stronger and avoids a boundary-continuity shortcut. Assume the zero-setup physical/hull optima exist and F is finite on their hull domain, as in the compact/lower-semicontinuous framework. Let q_m be the joint image of z_m and M=max_m J(q_m), which is finite. If p is a zero-setup physical optimum on layer m, its constructed approximation has value at most (1−epsilon)D_0+epsilon J(q_m). Consequently

`0<=D_tau−D_0<=epsilon(M−D_0)`.

For a zero-setup hull optimum represented by a finite complete-plan mixture, approximate every component with the SAME epsilon. The resulting hull point is (1−epsilon)p_hull+epsilon q_mix, where q_mix is a mixture of the slack representatives. Convexity gives J(q_mix)<=M, hence

`0<=CH_tau−CH_0<=epsilon(M−CH_0)`.

These estimates refer to the true positive-tau infima, sandwiched by inner-feasible and outer-zero-setup values. They allow signed prices and common affine wear. In particular, if the nominal gap is positive, then for sufficiently small tau it remains positive: D_tau>=D_0 and CH_tau<=CH_0+epsilon(M−CH_0). This is conditional local persistence, not an exact gap formula or a positive-tau support/attainment assertion without its additional framework qualifications.

For physical-value convergence alone it can suffice that at least one zero-setup physical optimizer has such an approximable same-layer construction. For hull-value convergence it can suffice that one optimal mixture has approximable components. Full projected-set convergence is the stronger assertion and the stated all-nonempty-layer slack condition is a transparent sufficient condition for it.

## Why strict slack cannot be assumed

Take n=1, B=1, a=b=3/4, alpha=delta=1, K_c=K_d=1/2, H=2 and fee f=1. The single paired bus requires at least C=1/2 early grid purchase. Its zero-setup polygon is the singleton C=1/2,X=0: the directional-time bound is saturated, and any export would consume still more time. Its joint point is(E,L,c)=(1/2,1,1).

For EVERY tau>0 this paired layer is infeasible. The required purchase alone takes a full early window at maximum power, and at least one nonzero action adds a strictly positive setup. No alternative cycle or action partition can shorten that transfer time.

The two-standalone-bus layer remains feasible for every tau: take no early actions and replenish each bus terminally, total grid energy3/2<=H=2. For the coordinatewise strictly increasing linear supply objective F(E,L)=E+L, lossless full replenishment fixes F=3/2 for all fleets. Thus

`D_0=CH_0=5/2`, while `D_tau=CH_tau=7/2` for every tau>0.

This is a nonvanishing value jump despite an always-feasible whole problem. In joint load/cost space, the disappearing fee1 point cannot be approximated by fee2 standalone plans; the full projected set does not converge either. It is not a positive-gap example, since the objective is linear and physical/hull values agree at each tau. It directly demonstrates why retained empty/boundary layers cannot be waved away.

More generally, if every point in a nonempty W_m has ell=1, every realization needs nonzero early transfer taking at least the whole window even before setup. That layer disappears for any tau>0. A strict-slack representative is therefore a substantive feasibility premise, not a cosmetic regularity condition. A disappearing layer may be irrelevant for a particular optimum, but that must be established separately; it cannot justify a full-set convergence claim.

This result is an analytical inner approximation and conditional convergence argument. It is not a new implementation qualification, empirical switching model, general positive-tau exact hull, runtime guarantee or public-certificate transfer.

## Subsequent comparison with the independently prepared candidate

After completing the derivation above, read `SWITCHING_TIME_APPROXIMATION_CANDIDATE.md` as newly authorized. Its inner/outer inclusion, per-layer slack interpolation, infimum treatment, lossless/wear caveats and separate no-slack counterexample are consistent with this independent result. No minimum-R exactness for positive tau is inferred: minimum-R supplies the physically constructed INNER polygon and the setup-free OUTER polygon, while the true setup-constrained set stays between them.

The candidate's sharper common error allowance is CORRECT. If J is M-Lipschitz on the complete outer joint hull in one declared norm and eta=max_m(lambda_m diam(Y_m^0)), both increments satisfy

`0<=D_tau−D_0<=M eta`, `0<=CH_tau−CH_0<=M eta`.

Their difference therefore lies in[−M eta,M eta], not merely[−2M eta,2M eta]. Thus `|Delta_tau−Delta_0|<=M eta` and Delta_0>M eta suffices for persistence. Infima and near-minimizers suffice; no unproved true-set compactness or attained positive-tau optimizer is required. The candidate appropriately does not deduce Lipschitz continuity just from closed convex finiteness at boundary points. Its common norm must include a fixed scaling for both energy and monetary coordinates, as it notes.

One small wording clarification: distinguish an anchor NOT SUPPLIED from an anchor that DOES NOT EXIST. In this particular normalized polygon model, existence of a zero-action point implies h=0 and therefore supplies strict occupancy slack. If every point of a nonempty layer has h=1, that layer really disappears for every tau>0. Other layers may still preserve a particular value, and the chosen A_m may be conservative, but zero-action points are not an exception to the existence-of-anchor statement. This does not affect the main theorem or its gap estimate.

A short conditional paper corollary is warranted: it quantifies a genuine omitted constraint using constructive feasible schedules, while the counterexample prevents an unconditional robustness interpretation. State the slack premise, inner/outer status and fixed-instance error bound prominently. It should remain a modest analytical consequence of the finite-action theorem and classical convexity/Lipschitz reasoning, with no new experiment, exact positive-tau hull, public-case transfer or empirical switching claim.
