# Positive per-action setup time: a controlled inner approximation

**Status: PROVED with an explicit occupancy-slack premise; unconditional convergence is false.** Analytical source-only result, not implementation or empirical qualification. No data, execution, imports, tests, hashes or literature retrieval. This is a constructive approximation consequence of the full polygon theorem and classical convexity/Lipschitz bounds, not generic switching-time exactness.

## Outer and physically valid inner sets

Retain the full common-loss model with positive direction powers K_c,K_d, a unit early window, B>0, common efficiencies, an existing assigned fleet, no other draw and unchanged charge-only terminal window. Now EVERY nonzero early charge/export action incurs a setup duration tau>=0 on the shared connector; no energy is exchanged during setup. It consumes time regardless of whether the preceding action had the same direction. There is no additional setup fee, minimum energy/duration, depth-dependent wear or service timing freedom. All buses are available throughout the early window. Common affine grid-throughput wear is allowed in the joint cost image.

For cardinality m, N_m=2n−m, let W_m be the previously exact, setup-free polygon with occupancy

    h(C,X)=C/K_c+X/K_d <=1.

Keep all its other four halfspaces and the affine image y=(E,L,c), including wear if used. Let Y_m^0 be its image, and Y_m^tau the TRUE projection of every size-m matching with setup time. Necessarily Y_m^tau is contained in Y_m^0: ignoring setup and replacing its matching by minimum r_m is a valid outer argument. It does NOT prove that minimum r_m remains an exact statistic for setup-constrained schedules.

The existing construction realizes every W_m point using at most

    A_m=N_m+2 ceil(2 alpha K_c/B)

nonzero EARLY actions. Its purchase/export duration is exactly h. Therefore the smaller polygon

    W_m^in(tau)={x in W_m: h(x)<=1−tau*A_m}

is physically attainable with setup: execute the same finite action list with one setup immediately before each nonzero action. Total time is h+tau*A_actual<=h+tau*A_m<=1. All setups are energy-neutral, cycles preserve their old SOC, and terminal scheduling is unchanged. Thus its image lies in Y_m^tau. It is a sufficient inner set, not an exact representation of all setup-feasible schedules.

## Slack-anchor theorem

Assume a given nonempty W_m has an anchor z_m satisfying h(z_m)<=1−epsilon_m with epsilon_m>0. If tau*A_m<=epsilon_m, put lambda_m=tau*A_m/epsilon_m in[0,1]. For EVERY x in W_m define

    x_tau=(1−lambda_m)*x+lambda_m*z_m.

Convexity preserves all other battery/terminal/resource halfspaces, and affine occupancy gives h(x_tau)<=1−lambda_m*epsilon_m=1−tau*A_m. Hence x_tau is in the physical inner set. The entire construction uses the SAME minimizing matching for the cardinality, not different matching labels at different aggregate points. No reserve slack or extra charging is presumed: the stipulated time slack and the convex polygon provide the required adjustment.

Let y=Phi_m(x), a_m=Phi_m(z_m) under the full affine LOAD–COST map. Then y_tau=(1−lambda_m)y+lambda_m*a_m and

    ||y_tau−y|| <= lambda_m*diam(Y_m^0).

This remains true for a lossless/noninjective load map, provided the cost image retains wear. Alternatively use (C,X) distance and the norm of the affine map. State the norm/scales when combining energy and monetary coordinates; an unqualified numerical diameter would mix units. Every outer point is thus within this distance of a real setup-feasible point, while every true setup point is already in the outer projection. A degenerate point or segment causes no difficulty IF it has the stated occupancy slack. An empty cardinality is skipped explicitly, not assigned an artificial anchor.

## Economic value bounds

Let J(y)=c+F(E,L) be M_m-Lipschitz on the relevant compact projected domain. For fixed cardinality, with outer and true optimal infimum values v_m^0,v_m^tau,

    0 <= v_m^tau−v_m^0
      <= M_m*lambda_m*diam(Y_m^0).

Choose an outer optimum (or an arbitrarily near optimum), map it as above, and use physical inner inclusion. This needs no monotonicity or price-sign assumption, only the stated Lipschitz control; bounded gradients on a neighborhood of the domain suffice. Do not infer Lipschitz continuity merely from a closed convex objective being finite at feasible points.

For convex J finite on the polygon, there is also the simpler fixed-layer bound

    v_m^tau−v_m^0 <= lambda_m*(J(a_m)−v_m^0),

by evaluating J on the convex combination. This can avoid an arbitrary norm/diameter constant. It is a bound, not the exact setup optimum.

If EVERY nonempty outer layer has an admitted slack anchor and tau*A_m<=epsilon_m, the whole physical objective error is bounded by the maximum of these layer allowances (or the allowance of an outer-optimal layer when that layer is known). Thus it tends to zero as tau decreases to zero for this FIXED instance. For complete-plan hulls, replace each outer component by its inner image with unchanged mixture weight; the mean displacement is at most max_m lambda_m*diam(Y_m^0). A Lipschitz J on the whole hull yields the corresponding hull-value bound. This is a new setup-constrained hull comparison, not a claim that an arbitrary mean plan is physical.

### Support-gap persistence with one error allowance

Choose one norm and let J be M-Lipschitz on the outer complete-plan hull, including its intrinsic-cost coordinate. Put eta=max_m lambda_m*diam(Y_m^0). Setup restrictions only remove physical plans, so, writing all values as INFIMA if needed,

    0<=D_tau−D_0<=M*eta,
    0<=CH_tau−CH_0<=M*eta.

For Delta_tau=D_tau−CH_tau, the difference of these two nonnegative increments lies in[−M*eta,M*eta]. Therefore

    |Delta_tau−Delta_0|<=M*eta,
    Delta_tau>=Delta_0−M*eta.

The sufficient strict-gap condition is Delta_0>M*eta, not a required2*M*eta margin. Both signs of gap change remain possible; restricting schedules need not increase the gap. Apply the established support implications only with their usual objective/domain/attainment qualifications.

The value proof needs no unproved compactness of the true setup set: it compares infima via explicit feasible inner points and finite mixtures, using near-minimizers where necessary. Under the present ideal finite-dimensional laws, compactness can also be justified for fixed tau>0: nonzero early actions number at most floor(1/tau), so there are finitely many bus/direction patterns. Each pattern has a bounded closed description allowing zero-energy slots; a zero slot and its setup can be omitted or reinterpreted as idle time without changing loads/cost. Terminal charge-only totals retain a bounded closed representation. Their finite projected union is compact. This observation would require restating the pattern law carefully in a formal theorem; the infimum argument avoids relying on it. It does not identify a minimal action pattern or algorithmic runtime.

## A decisive failure without slack

Take one service in each batch, a=b=B>0, alpha=delta=1, K_c=K_d=B and terminal H=B. The single successor edge and both standalone options are allowed. Full replenishment and the terminal limit require Q>=S−H=B, while early headroom gives Q<=P=B. Hence Q=B. With C−X=B and C/B+X/B<=1, necessarily C=B,X=0. This holds on BOTH cardinality layers. The setup-free model is feasible, but every schedule must deliver positive early energy B at power at most B, occupying the ENTIRE early window. Any tau>0 adds at least one positive setup duration, so the setup model is infeasible even with the two-bus alternative. Its value is +infinity rather than converging to the finite setup-free value. This uses no lost initial-inventory credit or alternate-route omission.

Accordingly, an outer singleton/face at full occupancy can disappear under arbitrarily small setup. Absence of a slack anchor does not always imply failure—zero-action points need no setup, and the constructive A_m may be conservative—but it blocks this guarantee. If tau*A_m>epsilon_m, clipping lambda to1 does NOT prove the advertised inner time bound; retain unresolved/no-guarantee status instead. An empty inner polygon does not prove true infeasibility.

## Usefulness and limits

The result is nontrivial in one precise sense: it converts a physically explicit finite-action construction into a quantitative allowance for a real omitted constraint, with feasible aggregate decisions rather than a formal penalty. It does not remove setup time exactly or give a radius without an instance-specific occupancy-slack proof. Action counts may be large and bounds weak. It does not establish uniformity across growing fleets, preserve the same optimum/matching/corners, transfer the old efficient-Z formulas, handle intrawindow prices/history-dependent degradation, or validate any public schedule. The public varied-time model has neither this common-window geometry nor an admitted global slack anchor, so none of its energy-law/certificate conclusions transfer through this argument. Independent review is required before manuscript use; no new experiment is justified by the bound alone.
