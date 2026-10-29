# Evidence map for the focused theory draft

This map separates mathematical claims, internal implementation checks and
the single public-case certificate. It is not a claim of external replication.
All repository paths below are relative to the research checkout. Existing
attempt folders and consumed sources are immutable; reproduce only through a
separately scoped fresh namespace, never by resubmitting a closed attempt.

## Analytical claims

- `framework.tex` states the classical complete-plan support/convexification
  argument used by the paper. This is prior art, not the novelty claim.
- `heterogeneous.tex` and `heterogeneous_proofs.tex` derive the exact joint
  early-load/used-bus-cost projection under the stated two-batch, allowed-graph,
  shared-resource and full-refill assumptions. The sorted shortcut requires
  a complete crossmatching graph.
- `v2g.tex` changes the thresholds for lossless bidirectional charging with
  gross connector accounting and equal purchase/export settlement. Persistence,
  restoration and capped idle-bus arguments have independent analytical reviews
  in `research-20261029/public_support_resolution/V2G_EXTENSION_REVIEW.md`.
  The separate losses assessment/review explains why the scalar classification
  cannot simply be transferred to inefficient charging.
- `construction.tex`, `expansion.tex` and `ownership.tex` retain the accessible
  specialization, alternative-duty/equipment distinction and ownership effect.
- `certificates.tex` exposes the standard exact tangent/residual, infeasibility
  and branch-coverage algebra used in the public certificate. Its independent
  review is `CERTIFICATE_APPENDIX_REVIEW.md`.

Proofs establish continuous-domain claims. Literal implementation comparisons
do not substitute for a proof. The heterogeneous eight-case qualification has
an adequate parallel-connector policy; the fourteen-case shared-connector
qualification is a separate complete-graph study. Neither is a numerical
qualification of every sparse graph or of the analytical V2G extension.

## Public depot-15 certificate chain

| Object | Exact revision or artifact milestone | Scope |
|---|---|---|
| Public case descriptor | `253c1e29295e766b3889fc8f5c28d9808e00b3d6` | One37-service base, declared synthetic energy and economics |
| Energy-flow/exact-dual semantics | `3278d50f8323618bd36809b1bbb1a0da081e23ff` | Independent model reconstruction and exact row arithmetic |
| Rational physical witness | artifact `0cb3c54de6e8e5c391afb37bcbb68ad3a51925ee`; authority `3cbb8c9d965e9222ef8a98191bf775b4925382a1` | Strict physical upper441.532912… and fixed-route charging optimum |
| Admitted response and two-plan mixture | artifact `f5ec2aa5770188d173af7297620a5fcea99fef9a`; authority `c5f056b90ca895786c44f96903cdaafff97fce52` | Feasible CH upper; no mixture-global-optimum claim |
| Physical branch search/checker | source `6a171357b65254b52cade63ed95dcce798485f36`; control `6bdcf254`; artifact `ef0e08203dba5ac2ddcaff6bd8639cc9a70677b9` |303-node exact physical coverage plus fleet-count exclusions |

Compact results, interpretation reviews and final resource receipts live in
the respective `research-20261029/public_*` packages. The definitive accepted
inequality is recorded in `public_support_tree/attempt01/results.json`:
CH<=441.142238, D>=441.151027 and exact-difference D−CH>=0.008790, with
proper outward displays. The exact rationals, not these rounded numbers,
decide strict separation. D<=441.532913 is the safe six-decimal physical upper.

The source-bound mixture is admitted separately from the lower certificate.
The quadratic two-bus tree covers physical plans; the one-bus obstruction
and three-plus fee/mandatory-energy floor complete its physical domain.
It must never be used as a lower bound on CH or to exclude higher-fleet
mixture components. No native OPTIMAL label or failed raw integer candidate
is promoted into an exact physical witness. All prior strict-replay failures,
failed multiplier recovery and time limits remain in the evidence history.

The model-to-certificate inclusion is stated separately in
`MODEL_TO_CERTIFICATE_REVIEW.md`. Every schedule using the descriptor's fixed
declared movement modes maps to its binary cover, per-leg inventory and
continuous charging-interval rows with identical load and operating cost.
The interval partition uses all declared window/resource/market endpoints,
not an energy sampling grid. The derived fleet cut is necessary under that
same access policy; direct/pullout modes admit no implicit charging.
The descriptor's fleet cap, fixed leg times/energies and depot/terminal charge
windows define the certified opportunity set. A complete directed deadhead
matrix alone does not prove completeness over arbitrary departure-time
choices, extra depot visits or other unlisted charging access. No such broader
operational completeness claim or data-to-mode generation audit is supplied
by this source-only mapping review.
The narrowly inspected generator chooses maximal via-depot gaps on the SAME
directed inbound/outbound arcs (immediate return/latest next departure).
Zero-draw depot waiting and nonnegative consumption justify timing/excursion
domination only with those travel alternatives fixed; they do not prove that
arbitrary multi-leg routes are dominated by a nonmetric matrix's direct arc.

## Reproduction and practical limitations

The recorded native environment uses Gurobi12.0.1 with one configured thread;
the exact checker uses rational arithmetic and source-defined semantics.
Complete native startup, search, admission, exact checking, serialization,
parent read and cleanup are paid in the package owner meters. Nested child
observations overlap those meters. The public tree cost1055.86displayedCPU
and1079.58elapsed seconds; all earlier discovery and failed stages remain
additional paid work, not an end-to-end speedup claim.

An independent reader can inspect the frozen sources, compact acceptance
records, exact arithmetic proof format and complete source/command/resource
manifests. An external reproduction with a fresh namespace and independently
obtained solver environment has not been performed. The current artifact
chain is not advertised as a turnkey, externally replicated benchmark.

The positive sign is for one specified charge-only model. Public timetable
data do not calibrate the energy or economic assumptions. The small certified
separation is not an estimate of operational prevalence or practical welfare
loss, and no substantive ML advantage is established by these certificates.
The learning guide/deck retain the separate model-capacity tests and their
strong classical baselines rather than presenting this theory as an ML result.
