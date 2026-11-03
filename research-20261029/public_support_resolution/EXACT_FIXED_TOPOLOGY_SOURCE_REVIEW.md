# Exact fixed-topology recovery: adversarial source review

Verdict: **Scoped mathematical/source PASS; no acceptance-soundness or definite
API blocker found for the stated fresh-problem/cached-callback contract.**
This does not qualify numerical recovery or guarantee a public topology will
recover within the declared limits. Read only exact_fixed_topology.py and
FIXED_TOPOLOGY_RECOVERY_DESIGN.md. No actual data, imports, tests, hashes,
native solve, commit or new agent. One output-counter clarification was added
to the source; no algorithm or certificate condition was changed.

## Charge-only projection

The complete selected path cover is recovered before charging variables are
built, with exact mandatory coverage, fleet cap, no repeated/disconnected
components and all selected IDs retained. The semantic callback supplies the
original validated full-case elementary interval partition, not a selected-
topology repartition. Thus output allocation indices agree with the original
verifier, and charging opportunities outside selected visits are not introduced.

For each path, inventory is B minus exact cumulative consumption plus eta
times previous visit charges. Every leg and service prefix is checked. The
inbound leg immediately before a depot gap supplies its pre-charge check;
the post-charge check supplies headroom before outbound legs. Pull-in charging
is checked after all inbound legs, and separate per-bus final equalities force
full replenishment. Nonnegative consumption and monotone charging justify
checking these boundaries. The shared elementary capacities and individual
finite q boxes are sufficient under the original single-connector, homogeneous
rate, zero-switching, no-parked-draw assumptions. Same-bus selected windows
cannot overlap in their interiors because they lie on chronological paths.
The resulting q-only system is an exact fixed-path charging reformulation.

The old terminal-only construction's nonterminal headroom failure is therefore
not something this method ignores: the QP includes every earlier visit and
prefix and may change nonterminal allocations. It is a different recovery
algorithm requiring its own prospective native proposal and exact admission,
not an automatic repetition of the failed terminal rule.

## Affine face, singularity and dual signs

The face tolerance only proposes coordinates/equalities. Exact elimination
detects inconsistent rows; sorting pivots forward and solving backward is
consistent with the sparse echelon representation. Free KKT coordinates are
seeded rather than incorrectly assumed unique. The stated Hessian is the
correct positive-semidefinite load aggregation Hessian: b_t for two q variables
in the same period and zero otherwise. A stationary equality-QP solution is
an affine-face minimum, even if its charging vector is nonunique.

That restricted-face fact is not used as the final optimality proof. The code
checks every original finite bound and every prefix/resource/refill row exactly.
It then retains all tight nonzero original rows for dual recovery, including
dependent inequalities. A primal row basis is not mistaken for the signed
dual opportunity set. Zero-coefficient tight rows have zero RHS and can safely
receive multiplier zero; infeasible constant equalities already fail primal
checking. Multiplier signs and complementarity are checked for every row.

Seeding a degenerate dual family can choose wrong-sign multipliers despite
existence of a valid alternative. Likewise the one selected face can fail.
Those are incomplete-recovery outcomes, explicitly not topology infeasibility.
No unregistered sign-feasibility LP, alternate face or tolerance search occurs.

## Exact whole-QP optimality and physical admission

With g_j=a_t+b_t*load_t and rho=g-A^T*pi, the finite-box residual lower
certificate has the correct minimization signs. For every coordinate,
including proposed zeros and bound variables, the code requires
rho_j*q_j=min(rho_j*l_j,rho_j*u_j). Exact row complementarity and the
tangent constant ops-sum(b_t*load_t²/2) give the correct global fixed-QP
lower bound. Requiring its equality with the exact primal objective is
sufficient for whole fixed-topology optimality, even if an earlier face-
selection or KKT step was unhelpful. Native OPTIMAL or small residuals are
never substituted for this equality.

Only afterward is the original physical callback invoked once. Strict pass
and exact objective agreement are required. Under the specifically admitted
original verifier, strict_pass also entails the physical/upper flags; the
callback must not be replaced by an arbitrary object returning those fields.
The problem must be built fresh from admitted case/topology sources; recover
does not semantically authenticate an externally supplied serialized matrix.
Those are material worker/owner obligations before a frozen attempt.

## Guards, diagnostics and prospective limits

Dimension guards are applied before reduced primal/dual systems, not to the
full graph. In particular ALL active original dual rows count toward the
250-dimensional dual cap: many dependent tight rows can make recovery fail
even with a small primal basis. A dense native interior proposal can likewise
leave more than250 nonzero q coordinates. Neither condition licenses dropping
rows or retrying another method without a new authorized design.

Time/operation/bit guards are checkpoint controls. Fraction construction,
temporary products, generator sums, matrix assembly, semantic reconstruction
and physical replay are not individually interruptible or all counted as
rational primitives. The source now records operation_counter_semantics to
make clear that exact_operations counts monitored checkpoints, not every
arithmetic operation. Outer process deadlines, memory observation and complete
serialization costs remain required. Recovery's local30-second clock excludes
build_problem and native proposal construction.

Useful nonblocking reporting improvements before freeze: retain the candidate
and failed replay packet if the final physical callback fails, and retain the
original proposed-active row names separately from the recomputed final tight
rows (the current face.proposed_active_rows names the latter). These do not
change correctness, but would make failure interpretation more transparent.
Validate frozen limit types/positivity in the owner; arbitrary malformed limits
or problem dictionaries are outside the current fresh-problem contract.

The future qualification should exercise singular Hessians, dependent active
inequalities of both senses, zero/bound q residual signs, inconsistent faces,
full refill/headroom rejection and dimensional/resource failures. No such
literal tests were executed in this review. Global fleet optimum, complete-
fleet hull optimum and price support remain unproved by any fixed-path success.
