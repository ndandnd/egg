# Research status (rolling handoff)

Last updated: 2026-08-17. This is the single entry point for "where the
project stands"; update it whenever a phase closes or a gate decision is
taken. Decisions with rationale live in `DECISION_LOG.md`; operational
memory lives in `UNICORN_RUNBOOK.md`; the measurement design and evidence
contracts live in `MEASUREMENT_RESULTS.md` and `B2_STABILIZATION_SPEC.md`.

## Completed phases (all certified, audited, merged to main)

1. **Literature breadth review v1** (`ref/`): 323-record catalog, novelty
   matrix, brainstorm B1-B39; flagship = Chapter I package B1+B2+B3
   (chicken-and-egg as unstabilized Dantzig-Wolfe; stabilized negotiation;
   uplift accounting).
2. **Phase 0/1/2 measurement infrastructure** (`src/egglab`,
   `src/experiments`): certified EVSP oracle with full-precision replay
   validation, four economic regimes with certified adaptive convex
   approximation, fixed-point/cycle detection, preemption-safe
   transactional checkpoints, expected-count + replay audits.
3. **Synthetic measurement closeout** (`result/analysis/`,
   `doc/MEASUREMENT_RESULTS.md`): 596 certified cells; headline: naive
   tatonnement cycles essentially everywhere at moderate/strong feedback
   (0 fixed points across 176 damping cells at b in {0.01, 0.05});
   dictator dominance measured. Root-LP-to-MIP integrality gaps are LARGE
   and formulation-specific (medians 127-301 on the compact
   vehicle-indexed MILP) — they motivate, but do not measure, the B3
   convex-hull uplift z_D - z_CH.
4. **B2-A2 pilot** (job 80309, audit 81432): certified plain column
   generation, 12/12 cells certified in 16-30 oracle calls (budget 240),
   grounded by a tiny complete-enumeration gate.
5. **B2-A3/A4/A5 pilot** (jobs 91001/91002): stabilized CG (du Merle
   5-piece box, Wentges + project-prespecified auto-smoothing, proximal
   chord-PWL bundle), 36/36 cells certified, all solves OPTIMAL and
   replay-valid, no budget exhaustion.

## Current evidence (as of the A2-A5 pilots)

Verified medians from the certified pilot (canonical values in
`result/b2_pilot/<stamp>/`, produced by
`src/experiments/analyze_b2_pilot.py`):

- median TOTAL oracle calls to certificate: **A2 21.5, A4 29, A3 33,
  A5 33** — plain CG used the fewest, and total calls is the
  preregistered acceptance metric;
- **call decomposition (the refined finding)**: A2 clean calls 21.5;
  A3 17.5 clean + 15.5 stabilized; A4 15.5 clean + 13.5 stabilized;
  A5 17.5 clean + 15.5 stabilized. On CLEAN calls, A4 beats A2 on 11/12
  matched instances and A3 on 9/12;
- honest interpretation: **stabilization — especially A4 — does
  accelerate clean-master convergence, but its extra candidate calls are
  not amortized at this problem size** (T = 28, n in {8, 12});
- the preregistered acceptance bar (best stabilized method >= 2x fewer
  median TOTAL calls than A2) is REJECTED on pilot evidence; the kill-1
  signal is ACTIVE on that metric;
- wall-time caution: the first artifact set mixed wrapper elapsed time
  into solver-wall fields (wall_clean_s + wall_stab_s did not equal
  total_solver_wall_s), so its per-method wall comparisons are not
  citable; the corrected pipeline partitions solver-reported wall exactly
  once by regime/phase and enforces the identity. Call-count conclusions
  are unaffected. Artifacts must be regenerated under the corrected code
  before any wall-clock claim is made.

What survives regardless of the kill decision: the certified negotiation
machinery itself (any CG variant certifies z_CH where tatonnement provably
cycles), the B3 uplift intervals, and the equivalence-theorem framing.

## Open questions

1. Does the pilot's A2 advantage persist on the full preregistered
   b = 0.05 population (32 instances/method), or is it an artifact of 12
   instances and small duals dimensionality (T = 28)?
2. Does ANY damping-family member (A1), compared at matched budgets, come
   close to A2 on outcome metrics? (Certificates are A2's alone; the
   comparison is on outcomes.)
3. If stabilization dies, does Chapter I's algorithmic half re-scope to
   "memory beats memorylessness" plus the equivalence theorem plus uplift
   atlas? (See DECISION_LOG 2026-08-17.)

## Next gate

**Pilot closeout must land before any further compute**: the committed
artifact set under `result/b2_pilot/` (two-commit protocol; commit 2 is
generated from the raw pilot runs, which live only on Unicorn and the
operator's machine — `src/runs/` is gitignored by design). Then decide:

- Option A: stop stabilization; reframe around memory-vs-memorylessness.
- Option B: run ONLY the prespecified moderate/strong-feedback matched
  expansion (208 remaining A2-A5 method-cells) to give the kill decision
  its full preregistered denominator.

The 960-cell campaign (576 fresh A1 cells + full CG grid) stays PAUSED
either way.
