# Matching-pool pilot: a useful negative result

25 October 2026. Static interpretation of [summary.json](summary.json) and the
frozen pilot design only. No additional solve, replay, import, hash, test or
outcome-driven pool modification was performed.

The diagnostic completed, but its prespecified competence gate failed. On
`scale:50685:40`, the pool retained 173 of 1,507 movements and independently
replayed a three-vehicle plan in 1.507 seconds including receipt publication.
On `scale:50605:80`, it retained 273 of 6,042 movements and independently replayed
a 24-vehicle plan in 12.441 seconds. Every route-only cover contained three paths
in both cases. The recorded native status was OPTIMAL with restricted fleet
incumbent/bound 3/3 and 24/24 respectively. Case receipts are linked explicitly
in the summary; all artifacts and negative flags remain unchanged.

The 80-trip native solve took only 0.746 seconds. Subject to the existing native
numerical tolerances and validity of that bound, the restricted model was solved
to its reported fleet optimum. This supports inadequate allowed connections,+rather than an exhausted search budget, as the immediate limitation of this
particular pool. Extra time on the same frozen restricted model is not the
principled next step. The known full-case five-vehicle witness is unmatched
historical context, but it makes the failure to preserve useful alternatives
concrete; this is not evidence that the full physical problem needs 24 vehicles.
The restricted numerical bound is neither a full-model bound nor an exact
mathematical optimality proof.

The source explains why three topological paths are insufficient: matching
accounts for local chronological adjacency; the secondary capacity score is a
single-movement maximum. Neither tracks battery state over a complete route,
terminal replenishment, or contention among routes for shared charging resources.
Retaining every parallel mode of the chosen pairs protects local alternatives,
but cannot restore useful trip-pair connections omitted from the three covers.
The joint physical model correctly rejected those optimistic route combinations
and used many more boundary starts. These are mechanism-compatible explanations,
not an identified cause: this bounded review did not inspect selected routes or
constraint activity and cannot apportion the loss among accumulated SOC,
replenishment, shared contention, or missing connection combinations.

There is also a major **candidate-density confound**. The 80-trip pool retained
only 113 of 5,882 flexible modes, approximately 1.92%, plus all 160 boundaries.
The historical learned policy retains approximately 30% of flexible modes with
structural floors. Thus this pilot cannot attribute failure uniquely to matching,
SOC or the charging-capacity proxy, or support a comparison with learned pruning.
It changed both the selection principle and the number of available choices.

The first next control should therefore be a **separate prospectively frozen,
density-matched classical pool**, before a resource-constrained route-generation
rewrite. Preserve the covers and fill to a common declared flexible count K
using the existing charging-aware CA1 or cheap-cost ranking; compare with the
same-K classical ranking control under identical physics, solve and total paid
budgets. Keep the same mandatory boundaries/backbone and declare how covers enter
the mandatory set. Choose a common K large enough for every mandatory set before
new outcomes, rather than silently enlarging only one arm. This is a new control
for a specified confound, not a resumed attempt01, automatic expansion or tuning
until the five-bus target is reached.

`classical_controls.select_connections` already defines the common structural
backbone and K as at least 30% of flexible modes, and `ca1_score` supplies a
charging-opportunity ranking. Its current selector has no caller-supplied
mandatory-cover argument; retaining covers requires an explicitly reviewed thin
research selection policy, not an assumption about the existing API. No such
policy was implemented here.

If a density-matched control remains poor, resource-aware route generation is a
principled later direction: retain nondominated prefixes carrying time, battery
state and charging-window alternatives rather than one topological predecessor.
Individual-route feasibility still does not establish joint feasibility; original
shared-resource selection/charging and full-case replay remain the admission
gate. A nearby existing primitive is
`route_fixed_repair.decode_path_cover(case, logits=None, cover_policy='cost_only',
energy_relaxation=True, charging_caps=True, shared_charging=True, ...)`.
Its documented SOC/energy/grid rows are necessary relaxations, not complete
physical feasibility, and this is a compact cover MILP, not a ready-made
resource-constrained shortest-path generator. Any use needs its own bounded
protocol; no new solve is authorized here.

This remains a conventional classical-control development step, not a novel
GRASP algorithm or a claim that learning is necessary. The two exposed cases,
different objectives/default solver seed, and unmatched historical allocations
cannot establish comparative performance or generalization. Preserve this
failed gate; do not resume, expand or tune attempt01.
