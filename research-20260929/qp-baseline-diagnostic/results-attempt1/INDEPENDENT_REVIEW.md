# Independent result receipt check

**Disposition: pass; no receipt or cell-accounting blocker.** The attempt manifest covers exactly 49 files; all sizes and SHA-256 values match, with no missing or extra files. The summary accounts for all six declared cells. The supervisor returned 0 without timeout, its process group is quiescent with a stable seal, and frozen source hashes are unchanged. The sibling wrapper reports successful freeze, preflight, and supervise phases, return code 0, and the requested one-CPU / 8192-MB allocation.

All six cells have on-time successful receipts and complete assessed evidence with native lower and upper bounds. Each raw result carries `numerical_qp_proposal`, denominator `10^9`, maxiter 500, cold arm, the correct state index, and the 10-second reserve. Recomputed state identities match all six results. QP proposal non-success counts are zero throughout.

| Case size | `source0`: status, pricing calls, max bits, QP proposals | `target`: status, pricing calls, max bits, QP proposals |
|---|---|---|
| n08 | certified, 5, 273, 4 | certified, 2, 204, 1 |
| n16 | certified, 10, 269, 9 | certified, 2, 211, 1 |
| n24 | certified, 6, 262, 5 | certified, 3, 212, 2 |

The frozen QP design matches the prior cold-baseline design on all six cases, physical and market identities, execution order, budget, reserve, and child cap; only the declared QP master policy and its denominator/iteration controls differ. The earlier native-LP screen had three source0 `budget_exhausted` outcomes and certified target rows. The QP screen certified all six. This is a positive result for the tested generated development cases, not evidence of a general speedup or expected behavior elsewhere. These remain native solver / physical-replay tolerance-conditional enclosures; `_exact` values encode stored rationals and do not certify the ideal hull.

This review used manifest, summary, frozen metadata, receipts, and assessed/raw result metadata only. No event JSONL, solver, cluster command, or test rerun was used.
