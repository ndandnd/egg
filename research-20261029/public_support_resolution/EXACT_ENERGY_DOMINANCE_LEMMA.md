# Exact stored-energy sufficient conditions for canonical dominance

Prospective analytical result, not a finding about the public coefficients. This note reads CANONICAL_GATE_SPEC only. It evaluates no instance, coefficient, artifact or floating function. The conditions below may fail on rounded stored values; no tolerance or coefficient replacement is authorized.

## Define the larger opportunity set first

Let a finite directed primitive-arc model have a selected charging depot d, exact nonnegative travel times tau_ij and exact nonnegative battery consumptions q_ij. Each paired (tau,q) arc is available by model definition, independently of any empirical road-path claim. Times satisfy directed triangle inequalities. Waiting at d consumes zero; waiting at EVERY other location consumes exactly rho times elapsed time, with one common exact rho >= 0. Only d admits charging. Services, fleet, initial/full-terminal conditions, charging resources and access policies are unchanged. No additional task, service, energy gain or charging location is hidden in a walk.

All energies here are exact rationals if the stored binary coefficients are interpreted as exact rationals. There is NO assumption q_ij = traction times distance + rho tau_ij. In particular, evaluating a floating constructor formula again is unnecessary for the following lemma. Missing primitive q entries still require an explicitly declared source/model definition; emitted canonical legs do not supply a complete primitive table by implication.

Require common post-last-service charging access regardless of the label attached to a depot visit, as in the prior adversarial review. Canonical windows must be maximal (earliest inbound arrival/latest outbound departure), and canonical mode availability must already have been established. A selected-depot endpoint must be treated as a depot-access case, not as ordinary off-depot waiting. A second location called a depot receives no free waiting unless it is the selected d; otherwise the common waiting law below is false.

## Finite sufficient inequalities

Write w_ij = q_ij - rho tau_ij. Impose these two *energy* triangle families in addition to the time triangles:

1. q_ij <= q_ik + q_kj on all declared locations.
2. w_ij <= w_ik + w_kj for all ordered i,j,k different from d, including repeated indices, with zero diagonal q_ii = tau_ii = 0.

Negative w entries are permitted. The second triangle family and zero diagonals imply no negative w cycle in the non-depot subgraph, so their use does not silently exclude repeated walks. Both families are sufficient, not necessary. Family 1 is used for a prefix ending at d or a suffix starting at d; family 2 is used for an entire service gap with no visit to d.

The actual stored canonical coefficients must separately satisfy the following finite comparisons for EVERY applicable service boundary and mode:

- A canonical inbound/pull-in energy Q_in <= q_id, and canonical outbound/pullout energy Q_out <= q_dj, with their declared direct-arc timing. These are exact coefficient comparisons, not formula identities.
- For a no-depot direct gap of total duration T, from service endpoint i to next service start j, its stored total C_ij(T), including its stored stationary wait, satisfies

  C_ij(T) <= q_ij + rho (T - tau_ij).

  The canonical gap must be a noncharging, nonnegative-consumption evolution with that total. The canonical wait location must be off-depot; depot endpoints instead use the admitted depot-access representative.

The same comparisons apply to any additional stored component needed by a pullout/pull-in representative. All canonical SOC trajectories must have nonnegative consumption between service boundaries or charging windows. Mandatory services likewise have nonnegative consumption with no in-service regeneration or charging. Checking just a mode's total is insufficient if that mode can contain energy gains, extra charging or mandatory intermediate inventory constraints.

These conditions accommodate rounded primitive weights and rounded canonical totals directly: each side is evaluated in its OWN declared exact representation. They do not assert equality to an unrounded traction/auxiliary formula. A wrong-sign rounding residual causes this sufficient gate to fail, even if arbitrarily small.

There is a separate inclusion issue: a strictly smaller stored canonical total need not be a trajectory of the uniform primitive/linear-wait law. To obtain an actual extension of the old set, either verify exact compatibility with that law, or explicitly retain the old canonical gap alternatives alongside primitive-walk gap alternatives. In the latter model, an already canonical gap is left unchanged and the proof replaces only primitive-walk alternatives. It does NOT allow arbitrary splicing of discounted canonical components into primitive walks without proving their energy lower bounds too. Calling the two laws identical would be incorrect.

## Lemma and proof

Under the assumptions and finite inequalities above, every feasible broader modeled walk schedule has a canonical schedule with the same fleet and service order and componentwise no greater grid purchases. Consequently, coordinatewise nondecreasing supply costs have the same physical and convexified infimum values in the canonical and broader sets, provided the canonical schedules themselves are admitted in the broader model.

For a gap containing no visit to d, write its walk's total travel time as t and its total duration as T. Every stationary portion is off-depot, hence total energy is

    sum q_arc + rho (T-t) = rho T + sum w_arc.

Repeated use of the w triangle gives sum w_arc >= w_ij. The stored canonical total is therefore at most the walk total. The time triangle makes its direct travel feasible within T. There is no charging in either evolution; since consumption is nonnegative, feasibility throughout follows from adequate SOC at the end of the gap and at the next service, not from a pointwise ordering of the two SOC curves.

For a gap visiting d, split at the first arrival and last departure from d. The q triangles imply that each travel prefix/suffix consumes at least its direct primitive q; all additional off-depot waiting consumes nonnegative energy. The stored canonical inbound/outbound comparisons therefore give no greater consumption. Time triangles place the old charging sessions inside the maximal canonical depot window. Delete all intermediate excursions and remain parked at d, where consumption is zero.

At the first old depot arrival the canonical bus has at least the old SOC. Retain the old charging clocks and rates until capacity would be exceeded, then curtail charging as necessary. With unit efficiency, no minimum session or taper, and no parked-depot draw, its SOC at old charging times is the capacity-clipped cumulative old purchases added to its larger initial SOC. Deleted excursions only consumed energy, so the new SOC dominates the old SOC. Its no-more-costly outbound suffix preserves feasibility of the next service. The same argument handles earliest final return and full terminal refill; latest full pullout removes unnecessary pre-service consumption. Apply this successively across services. Each bus's purchases are only curtailed at their original clocks, so shared power/connector feasibility and every grid-period component are preserved. No triangle assumption about service energy is needed because mandatory services are unchanged.

Canonical inclusion gives one direction of each infimum inequality. The constructed componentwise-dominating replacements give the other direction for monotone supply costs. Replace each component separately in any finite convex mixture for the hull comparison. This proves value preservation, not equality of full feasible load projections or enumeration of zero-price ties. The assertion does not apply to negative-price objectives. Attainment requires the separate compactness/closedness assumptions already used for the support theorem.

## Why continuous rounded waiting is not automatically covered

The exact waiting law is substantive. An arbitrary reevaluation W(t) of a binary floating formula is not established to equal rho t as a real-valued function. Splitting a wait can change sum W(t_i), and infinitely many continuously chosen durations cannot be certified by checking the finite canonical waits alone. Finite additivity plus nonnegativity on all durations would itself force a linear waiting law; an independently rounded function generally lacks that property.

A valid generalization is to prove a global lower envelope W(t) >= rho_lower t for EVERY admitted off-depot wait duration, then use rho_lower in w and in the direct canonical-total comparison. Prefix/suffix still need nonnegative waits. The proof uses only that lower bound. It does not require canonical stored waits to equal the lower envelope. A bound inferred from finitely many sampled durations is insufficient. With arbitrary subdivision and unboundedly small durations, floating underflow/rounding may defeat a desired positive envelope; the law and domain must be explicit. A frozen finite timing lattice instead permits a separately proved finite-domain path/wait analysis, but that is a different opportunity set and is not supplied here.

Thus transparent finite energy conditions EXIST for an explicitly additive primitive-arc/linear-wait model (or a proved global wait envelope), without false exact-formula equivalence. They do not, by themselves, extend a model defined by unrestricted retiming of floating waiting functions. If the larger law, complete q table, access assumptions or stored-total comparisons are unavailable, retain the current finite-mode scope. Metric PASS and energy-formula provenance alone cannot close this gap.
