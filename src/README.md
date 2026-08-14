# src

Code for this project: experiment harnesses, price-formation loops,
stabilized-master wrappers, analysis scripts — runnable locally and on the
Unicorn cluster.

Boundaries and conventions:
- The EVSP-DR and evspv2g_dp solvers remain separate repositories and are
  called as *oracles* (see `ref/context/HANDOFF_PRICE_MAKER_20260814.md`
  Section 7); do not vendor their code here without an explicit interface
  and versioning decision.
- Every run must emit the provenance record defined in `result/README.md`
  and label its oracle exactness tier (fixed-realization exposure /
  re-realization / restricted pool / capped DP / completed exact pricing).
- Bibliography tooling lives in `ref/tools/`, not here.
