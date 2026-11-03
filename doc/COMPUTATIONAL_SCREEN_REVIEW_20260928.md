# Independent implementation review: computational development screen

**Verdict: PASS for implementation preflight only.** This review does not admit
any experiment output, certify scientific results, or qualify an ML evaluation.
No optimizer, freeze, cluster job, or public result was run as part of this review.

Reviewed files and SHA-256:

| File | SHA-256 |
|---|---|
| `src/experiments/computational_benchmark.py` | `da96e4601e34dc797526703db68c2d2cbda57d78a9048c8fd7c34889ffca1c8f` |
| `src/tests/test_computational_benchmark.py` | `e269d6801efcc06895aa229b8c4ee72ab6e6602692005e99b3f11770dc0ec24e` |
| `src/cluster/computational_benchmark.sbatch` | `55f3fa954b18c9abcb26d5cbe63c61926732f1a3c3b3b271e68ef9b60b0d5b3b` |
| `research-20260928/computational-design/IMPLEMENTATION.md` | `abb9d121f6758d08d91e5540dbb82fb17795f761af2f1b7af03f10da370dd86b` |
| `doc/COMPUTATIONAL_SCREEN_PROTOCOL_20260928.md` | `c952566307a51f3c585a0f6d94b2acf11f14d153039bcb22c11205ca35886b12` |

The fixed design contains four declared physical cases, two deterministic
market states each, and 32 planned stage cells. The two 37-service depot
variants share one development group. Freeze records exact case/market/budget
definitions, Python and solver-package versions, source commit, and source
hashes including `src/egglab/solver.py`. Complete-fleet hull columns and the
absence of an independent route-level master are explicit.

Stage dependencies now require successful on-time receipts and complete
replay evidence; retained import also checks the exact expected state-zero
market identity. Timed-out or failed stages cannot be relabeled from a
surviving native result. Partial result JSON is retained and reported as a
partial row. If the controller is interrupted, postmortem accounting covers
all 32 cells; the process group is checked before sealing, and uncertain
cleanup prevents a stable manifest claim. The Slurm wrapper receipt is stored
beside the attempt, outside its sealed manifest.

The protocol distinguishes the 5,400-second controller allowance, 5,500-second
supervisor-invocation cap, and two-hour allocation. Per-stage hard deadlines
include startup and export. Polishing's 20-second target is explicitly soft;
actual elapsed time and excess remain reportable, and the earlier strict
5-second failure is not reclassified. The outcomes remain development and
tolerance-qualified evidence, not exact ideal-model proofs, operational claims,
or evidence of learned-proposal efficacy. Any own-price regret is for the
replayed named planner incumbent, not an unknown optimum.

Validation: all 9 pure design/process-control tests passed in 1.56 seconds;
`bash -n src/cluster/computational_benchmark.sbatch` and an explicit
trailing-whitespace/final-newline scan passed. Tests cover fixed identities and
budgets, stage eligibility, timeout labeling, nested-process cleanup,
truncated-result reconciliation into 32 rows, and refusal to seal when
process-group quiescence is unconfirmed.
