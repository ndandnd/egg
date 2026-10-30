# Pure selector and CA1 contract review

24 October 2026. Narrow independent static review of the classical-control specification, relevant study selection rule, new `classical_controls.py` and symbolic tests. No execution, runtime import, solver, native/ML/comparison launch, fixture generation, protected data, source edit or core requalification. The historical study addendum's pending qualification-cap text is superseded by current approved accounting.

## Source verdict

No concrete implementation blocker found. The selector constructs a common price-blind incoming/outgoing top-three union using the frozen heuristic and movement-ID ties. Arm scores fill only outside that backbone. Integer arithmetic computes exact ceil(3M/10); K includes backbone size, all boundary movements remain outside the flexible count, original movement order is retained, and the original case is not mutated. Restricted-case identity and masks/IDs/hashes are recorded. Equal K controls count, not topology, solver difficulty or feasibility. Empty choice beyond the backbone remains a zero-exposure case.

CA1 uses usable battery `B-reserve`, separates battery demand from grid kWh through efficiency, and intersects only the declared depot-split gap with resource and market slices. Connector-zero periods contribute no capacity; direct/boundary movements receive no intermediate charging capacity. Resource power times minutes/60 has correct grid-energy units. It neither borrows charging outside the window nor allocates shared-fleet contention.

The proportional electricity proxy correctly uses total cost `a*q + b*q*q/2`, not marginal price `a+b*q`. Positive demand with zero capacity records shortfall/stress while returning the specified zero replenishment proxy; flags affect ranking rather than deleting edges. ALL leg durations enter the declared deadhead proxy. Signed `fsum` residuals, fixed tau, borderline diagnostics and deterministic integer score order match the frozen convention. Boundaries are explicitly unranked with aligned zero scores. Scalar feature ledgers, capacity hashes and tariff/case identity bind the inputs; nonfinite computed features fail closed.

These are optimistic local features and an unvalidated ranking proxy. Neither capacity margin, stress absence, common coverage nor proportional cost certifies feasibility, impossibility, realized fleet bill, unrestricted bounds or optimality. The module states that limitation; qualified replay/native code and trained assets remain unchanged. CF1 is outside this package.

## Source-bound check scope and budget

The31-case symbolic suite covers exact counts/ties/permutation, boundary preservation/nonmutation/restriction identity, score/tariff validation, hand-calculated split-period capacity and quadratic proxy, tariff/curvature response, zero connectors/window availability, direct capacity, numerical stress boundaries, unranked boundary scores, negative prices, stationary-leg duration, independent-edge contention limitation and nonfinite output rejection. The added multi-trip regression independently exercises incoming/outgoing top-three sets: their common six-edge union expands K beyond ceil(.3*15)=5, independent of opposing arm scores. Its static readback is clear.

Only one prospective solver-free check is in scope, provision40 s including supervision, ADMIN0. Carry **1293.1124853401802 s** plus40 ends **1333.1124853401802 s**, below1620 dispatch and1800 hard limits, retaining180 shutdown reserve. One worker/thread and5GiB persist. Actual check CPU, monitor/supervisor work and failures must be carried once; no fixture/native/ML/comparison launch follows automatically.

**Final source/test contract gate: clear for one fresh source-bound31-case solver-free check**, subject to final parent review/freezing of the stable check wrapper/protocol/inventory. No test was run by this reviewer. No new resource commitment, automatic retry or claim of classical-baseline performance is implied.
