# Independent review: cold budget-sizing diagnostic

**Disposition: no remaining launch-scope blocker found.** This review covers the design note, eight-cell driver, focused tests, and Slurm wrapper. No solver or cluster job was run.

The motivation is a stop-reason confound in the prior small multivisit comparison. Under the original market (four 0.20 intercepts, curvature 0.20), cold runs reached the four-pricing-call cap after four master calls. Under the changed market (0.18, 0.18, 0.22, 0.22; same curvature), legacy and reserve cold runs stopped after three pricing calls and three masters at the projected rational-polishing limit: 19 pairwise steps and roughly 0.35–0.40 s of polishing. The later matched comparison's reserve-cold row recorded 3974 maximum rational bits against a 4096-bit cap. The reused state-1 pool instead imported four state-0 columns and needed one fresh pricing call and one master. That comparison changes both initial support and pricing count, so it cannot isolate arithmetic. The new cold 2×2 call-cap/bit-cap grid in each market addresses those two budget limits while keeping the physical case, native-LP master, pricing method, and other controls fixed. Price trajectories may still diverge; the design correctly limits interpretation to factor effects, not a same-price-path decomposition or speedup.

The driver pins source files, exact case/market identities, portable runtime and a non-optimizing GRB seed-0 preflight; it records host separately. It launches the eight declared cells serially, cold, with no reserve, retained pool, cache, or warm start. Row admission requires a successful on-time receipt and replayed complete evidence matching the saved raw bounds. The incomplete-assessment path now records `incomplete_evidence` instead of promoting a `certified` label. Pricing/master component sums carry separate completeness flags; child wall time remains receipt-based, and missing components are not inferred. Timeout handling is 90 s, then TERM/10 s and KILL/2 s; late returns remain not on time. The 900 s controller, 1000 s outer cap, and 1200 s one-CPU/8-GB Slurm allocation have bounded headroom; the wrapper records setup and freeze/preflight failures. The node exclusion and no-requeue setting match the approved design.

Sol reports three focused pure tests, `bash -n`, and diff checks passing. Root plans source CI before any launch. This remains a single-seed development sizing diagnostic; no expansion, learning comparison, or performance conclusion follows automatically.

Reviewed SHA-256:

- Driver: `src/experiments/budget_sizing_diagnostic.py` — `2b9da59b1699133cd7b5ffdc2465d4e5e8fe0d6a7b4e25560f189a6c4fc7ce23`
- Tests: `src/tests/test_budget_sizing_diagnostic.py` — `79118d1a4465b3aa45a49f320ac9b9bc80f2f1eb785ed0f2eb630433d07b6b36`
- Slurm wrapper: `src/cluster/budget_sizing_diagnostic.sbatch` — `d5635444d4ece0720cd8569a34c68090fecff9e993ed72c998ac2bb0ca34011b`
- Design: `research-20260928/budget-sizing-diagnostic/DESIGN.md` — `8a79cb718bcf05e3545161d5d982a7f95735a2f6c2fcca7d77d96b13b6b49494`
