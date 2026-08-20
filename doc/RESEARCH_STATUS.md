# Research status (rolling handoff)

Last updated: 2026-08-18. This is the single entry point for "where the
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
6. **B2 full-population closeout**
   (`result/b2_full/20260818T140356Z/`): the 12 pilot instances plus 52
   expansion instances form exactly 64 matched instances per method and
   256 A2-A5 method-cells. All 256 certified within 240 calls; all
   provenance, replay, completeness, solver-status, scientific-setting,
   and corrected wall-partition gates passed.
7. **A6 burned pilot and arm selection**
   (`result/a6_pilot/20260819T005514Z/`): 24/24 implementation cells
   certified and passed the trigger-stream, replay, completeness, and
   solver-status audits. Under the frozen one-shot rule, `a6_a3` won only
   2/12 matched pilot instances, so **`a6_a4` is the committed holdout
   arm**. The pilot is burned development evidence, not an evaluation.

## Current evidence (full 64-instance matched population)

Canonical values are in `result/b2_full/20260818T140356Z/`, produced by
`src/experiments/analyze_b2_full.py`. The corrected pilot artifact remains
at `result/b2_pilot/20260817T225235Z/` as the historical pilot closeout.

- all methods certified 64/64; A3-A5 each certified 32/32 b=0.05
  instances, so acc-1 passes;
- median TOTAL calls: **A2 24, A3 30, A5 32, A4 34**. The best
  stabilized-to-A2 speedup is 24/30 = 0.80, so the preregistered 2x
  acc-3 threshold fails and kill-1 is active;
- median CLEAN calls: **A2 24, A3 16, A5 17, A4 18**. A3, A4, and A5
  beat A2 on clean calls on 54/64, 57/64, and 45/64 matched instances;
- median corrected solver wall: **A2 38.48 s, A4 43.59 s, A5 49.21 s,
  A3 57.08 s**;
- honest interpretation: stabilization accelerates clean-master
  convergence, but the extra candidate calls are not amortized at this
  problem size (T = 28, n in {8, 12}). The current A3-A5 variants are
  rejected as end-to-end total-call improvements, not as evidence that
  stabilization has no mechanism;
- all dictator/convex-hull consistency checks pass; the minimum
  `z_D_ub + tol_D - LB_CH` margin is 0.01.

What survives this decision: the certified negotiation machinery itself
(any CG variant certifies z_CH where tatonnement provably cycles), the B3
uplift intervals, and the equivalence-theorem framing.

## Open questions

1. On the frozen seeds 16-31 holdout, does selected sparse stabilization
   (`a6_a4`) satisfy the preregistered adoption rule against a fresh A2
   baseline: score ratio <= 0.85, at least 38/64 wins, and the two
   certification-rate gates?
2. Does any damping-family member (A1), compared at matched budgets, come
   close to A2 on outcome metrics? (Certificates are A2's alone; the
   comparison is on outcomes.) This campaign remains paused.
3. Does stabilization become amortized at larger dual dimension or
   physical scale? The completed expansion does not answer this because
   n in {8, 12} and T = 28 were fixed; any scale study requires a separate
   prespecification.

## B3 baseline (in review)

The no-solver B3 certified-uplift baseline restates the committed B2
population as one A2 interval per unique instance (64 rows), with A3-A5
as consistency witnesses whose four-way interval intersection must be
nonempty. Certified classification: 38 strictly positive, 21 strict zero
crossings, 5 exact-zero boundaries. Paired interval-subtraction effects
are heterogeneous (feedback 23/32 certified positive, workload 19/32):
stratum-level certification rates rise with n and b, but matched effects
are descriptive rather than causal. Retrospective/exploratory: see
`doc/B3_UPLIFT_BASELINE_SPEC.md` and `result/b3_baseline/`. No new
compute was spent.

## Next gate

The full-population closeout is COMPLETE and canonical at
`result/b2_full/20260818T140356Z/`. The prespecified decision is recorded
in `DECISION_LOG.md`: current A3-A5 variants are rejected on total-call
efficiency, while their population-wide clean-call advantage triggers a
focused continuation.

The focused continuation is specified in
`doc/A6_SPARSE_STABILIZATION_SPEC.md` (2026-08-18). A6 =
event-triggered sparse stabilization — A2's certified loop plus a
scheduler spending the seed call and then exactly one oracle call per
master iteration, chosen under the frozen priority T0 recovery > T4
initialization > T3 candidate stall > T1 closable gap
(theta_cert = 10*epsilon) > T2 staleness (K_MAX = 4) > default
Wentges-smoothed candidate. T0 forces clean calls through A2's direct
escalation/retry logic during ambiguity/refinement/duplicate recovery;
candidates never interrupt recovery. Certification remains clean-RMP UB
+ clean-dual LB only; skipped calls can never affect validity; terminal
states are certified, budget-exhausted, or fail-loud recovery error.
Method identities `a6_a4` (primary; clean-call wins 57/64, no stabilized
master) and `a6_a3` (pilot-only alternative). Pilot: exactly 24 cells on
the burned pilot instances, both arms 12/12 audited, one-shot >= 9/12
score selection committed as a machine-readable artifact BEFORE any
holdout work. Holdout FROZEN at seeds 16-31 (no substitution;
infeasibility halts and amends the preregistration), A2 + the selected
arm = 128 cells. Scoring: certified = calls-to-certificate, valid
budget-exhausted = 241, both-exhausted = tie, validity failures halt
unscored. Exhaustive decision partition: ADOPT (all gates) /
HALT-AND-DEBUG / FINAL NEGATIVE (certification shortfall, clear kill,
gray, discordant) — any final negative ends the stabilization line
absent new theory. All five review questions are resolved (spec Section
10). The 24-cell burned pilot is complete and its canonical selection
artifact is committed at `result/a6_pilot/20260819T005514Z/`:
`a6_a3` won 2/12, so the frozen holdout arm is `a6_a4`.

**Current step**: the first 128-cell holdout attempt (Slurm job 218143,
commit `2dba047`) halted unscored after 126 completed tasks and two matched
first-master failures at seed 26, n=8, b=0.05. Both failures were caused by
the same `-7.356248409800537e-06` kWh raw aggregate-load solver residual being
stored as a nonphysical negative master-column coefficient. Preserve that
attempt as incident evidence; do not score its 126 cells or repair only the
two failures. Merge the reviewed load-reconstruction fix, then launch a full
replacement of the same 128-cell population (64 fresh A2 + 64 `a6_a4`; seeds
16-31 x n {8,12} x b {0.01,0.05}) under one new pinned commit. The guarded
execution and closeout paths live in
`src/experiments/run_a6_holdout.py`,
`src/cluster/launch_a6_holdout.sh`, and
`src/experiments/analyze_a6_holdout.py`. Before any method cell, the
launcher requires a whole-population constructive feasibility proof for
all 32 unique physical instances. No `a6_a3` holdout cells, adaptive seed
substitution, or certification-count completion gate are permitted. No
completed-cell outcome table from the failed attempt was inspected before the
replacement decision. The 576-cell A1 campaign, the old 960-cell
campaign, and any scale experiment remain paused.
