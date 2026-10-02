# Independent review of the recoverable-pruning design

2 October 2026. A GPT-6.1 Sol writer prepared the [protocol](../protocols/RECOVERABLE_PRUNING_PROTOCOL.md). A separate GPT-6.1 Sol reviewer checked its conceptual design and completed text; the parent reviewed and integrated the result. No experiments or protected-data inspection occurred.

The material checks were:

1. A stored replay-valid fallback guarantees an available answer, not feasibility inside a restricted model. The design requires separate embedding checks, reference-preserving exceptions and no strict cutoff excluding that reference.
2. The Hamming arm counts omitted movement binaries predicted zero. Radius-zero equivalence requires matching assignments/exceptions plus a valid compact/full mapping; nested feasible sets do not imply finite-time improvement.
3. Reinsertion must restore complete charging and coupling blocks. Ordinary restricted-LP reduced costs neither resolve infeasibility nor certify preservation of an integer optimum. Full-LP recovery and integer screening have different requirements.
4. Time includes initialization, building, repeated solves, repairs and replay. No cross-arm incumbent sharing or free acquisition is allowed. The equally initialized full baseline is not a separate cold unseeded baseline.
5. Record continuous charging dimensions and memory alongside retained edges: full-model Hamming restrictions may save little construction or charging work.

The independent reviewer found these points addressed and verified the 50 CPUh allocation: 34.5 + 3 + 6 + 6.5. The parent added one further fairness correction: pruning-only score computation must not be charged to an unpruned arm that does not use it. Shared fallback computation still counts for all arms; cached overlap must not be charged twice.

The estimate of 34.5 solver CPUh depends on the actual 30-cell budget vector. Fallback availability, stage schedules, caps, quality targets and failure/censoring rules remain explicit launch prerequisites. This is a prospective design, not evidence that recovery improves schedules or that the envelope is sufficient in practice.

The later [contribution challenge](FINAL_CONTRIBUTION_CHALLENGE.md) required a matched nonlearned greedy widening arm after the shared numerical fixes. The unexecuted five-arm design above is historical: the amended protocol has six arms, 540 runs and an estimated 41.4 solver CPUh, with a prospectively recorded 60 CPUh ceiling. The parent checked the revised arithmetic and preserved scoring-overhead fairness. A separate learned-versus-greedy benefit gate now controls priority for broader training; it does not claim neural methods are necessary. No job or concurrency change accompanied the amendment.
