# Decision log

Dated, append-only. Each entry: decision, rationale, evidence, revisit
condition.

## 2026-08-14 — Flagship: Chapter I package B1+B2+B3

Ratified after the breadth review: the chicken-and-egg loop as
unstabilized Dantzig-Wolfe (B1), stabilized price negotiation with
certificates (B2), uplift/indivisibility accounting (B3). Rationale: only
candidate that unifies the EVSP-DR (price-taker) and evspv2g_dp (dictator)
assets with an unoccupied novelty cell (exact, duty-based, trip-covering
EVSP inside endogenous price formation).

## 2026-08-15 — Replay tolerance policy

Full float precision in stored solutions; replay audit tolerance
REPLAY_TOL_KWH = 1e-4 kWh; legacy replay_ok=false records individually
revalidated via exact-hash sidecars; only certified_equivalent resolves a
loop record (per-slot loads determine the next price state). Evidence:
runbook incident log; PR #12 review.

## 2026-08-16 — Measurement closeout accepted

596 certified cells; damping baseline certified as unreliable (0/176
fixed points at b in {0.01, 0.05}); dictator dominance and
integrality-gap results accepted as Chapter I's empirical motivation.
B2 experimental design (Section 8 of MEASUREMENT_RESULTS.md)
prespecified: methods A0-A5, bounds, certification contract, acceptance
and kill tests, 960-cell grid with 12-cell A2 pilot gate.

## 2026-08-17 — A2 pilot certified; stabilized stage implemented

12/12 A2 cells certified (job 80309, 16-30 calls vs budget 240; audit
81432 PASS). A3-A5 implemented against B2_STABILIZATION_SPEC.md with the
review-hardened certification contract (clean-RMP UB, clean-dual LB,
deferred pricing-gap escalation), 36-cell pilot launched.

## 2026-08-17 — 960-cell campaign PAUSED pending pilot analysis

**Decision**: do not launch the 960-cell campaign (576 fresh A1 baseline
cells + 384 full-grid CG cells) until the A2-A5 pilot closeout is
committed and interpreted.

**Rationale**: the 36-cell stabilization pilot certified 36/36, but the
early scientific signal points the OTHER way from the stabilization
hypothesis: A2 (plain CG) had the lowest median oracle-call count
(operator-reported medians: A2 21.5, A4 29, A3 33, A5 33). The
preregistered acceptance bar for stabilization (best method >= 2x fewer
median calls than A2 at b in {0.01, 0.05}) is rejected on pilot evidence,
and the preregistered kill test ("if A2 already meets the bar,
stabilization is not the contribution") is triggered. Spending ~10x the
pilot's compute to confirm a hypothesis the pilot already rejects would be
poor sequencing; the closeout pipeline (result/b2_pilot/) must first make
the evidence citable and byte-reproducible.

**Options defined** (choice pending the committed closeout):

- **A. Kill stabilization now**: reframe Chapter I's algorithmic half as
  "memory beats memorylessness" — certified plain CG solves the
  coordination problem tatonnement provably cannot; A3-A5 become a
  negative result documented from the pilot.
- **B. Preregistered matched expansion only**: run the remaining 208
  matched A2-A5 method-cells at moderate/strong feedback to give the kill
  decision its full preregistered denominator (the acceptance criterion's
  actual population) before writing the negative result. Cost is ~1/5 of
  the full campaign; the 704 other cells stay paused.

**Revisit condition**: after `result/b2_pilot/<stamp>/` lands (commit 2 of
the two-commit protocol) and the matched tables are reviewed.

## 2026-08-17 — Wall accounting corrected; decomposition finding recorded

**Decision**: fix the pilot-closeout wall split (the first artifact mixed
wrapper elapsed time into `wall_clean_s`/`wall_stab_s`, so their sum did
not equal the independently correct `total_solver_wall_s`) and expose the
clean/stabilized call decomposition in the artifacts; regenerate artifacts
under the corrected code before any further campaign. Total-wall F2 and
per-method medians from the first artifact remain valid and unchanged.

**Refined finding** (verified on the certified pilot): on CLEAN
certification calls, A4 beats A2 on 11/12 matched instances (A3 on 9/12)
— clean-call medians A4 15.5, A3/A5 17.5 vs A2 21.5 — so stabilization
DOES accelerate clean-master convergence; it loses only after its
candidate-call overhead (total medians A4 29, A3/A5 33 vs A2 21.5). The
preregistered acceptance metric remains TOTAL oracle calls; the kill-1
signal stays active on that metric, but "stabilization adds nothing" is
NOT the correct summary — "stabilization is not amortized at this
problem size" is.

**Next campaign designated (not launched)**: the prespecified 208-cell
matched moderate/strong-feedback A2-A5 expansion, to give the kill
decision its full preregistered denominator. Explicitly NOT a scale test:
it adds seeds at fixed n in {8, 12} and T = 28; testing whether
stabilization becomes useful at scale would require larger trip counts,
more slots, multiple fleets, or additional coupling rows — a separate
prespecification if ever pursued.

## 2026-08-17 — Option B chosen: 208-cell matched expansion implemented

**Decision**: run the 208-cell expansion (Option B) before any kill/reframe
writing. Implemented as `experiments/run_b2_expansion.py` + guarded
launcher: the remaining 52 moderate/strong instances (seeds 0-15 minus
pilot {0, 11, 15}) x A2-A5, settings identical to the pilots; launch
pending operator review of the launcher, then overnight Unicorn
submission.

**Prespecified audit gates**: completeness only (cg=208, 52 per method).
Certification is the MEASUREMENT (acc-1: >= 95% per stabilized method on
the full b=0.05 population; the 2x total-call criterion on all 64
moderate/strong instances per method) — gating on it would assume the
result. The clean/stabilized call decomposition from the corrected
pipeline (PR #19) is the secondary readout: whether A4's clean-call
advantage (11/12 on the pilot) persists population-wide.

**Decision rule after the data** (restated from 2026-08-17): if A3-A5
lose on total calls, clean calls, and wall across the matched population,
stop stabilization and reframe; if the clean-call advantage or a
b=0.05/degeneracy subgroup effect persists, prespecify a focused
continuation; the 576 A1 cells and any scale experiment remain separate
decisions.

## 2026-08-18 — Full-population analysis pipeline landed; verdict PENDING

**Decision**: analysis code for the 256-cell full population
(`experiments/analyze_b2_full.py`) is committed ahead of the data review.
Prespecified before looking at any expansion-derived table:

- exact union validation (12 + 36 + 208, no overlaps/gaps/extras, all
  identity hashes recomputed, per-root audits re-run programmatically);
- acc-1 evaluated on exactly 32 b=0.05 instances per stabilized method
  (96 method-cells); acc-3 on exactly 64 matched instances per method
  with the unchanged 2x total-call threshold; kill-1 from A2's 32 b=0.05
  cells plus the acc-3 outcome; all labels computed from tables;
- two-call cells (seed + one certifying clean call) are legitimate
  immediate-certification outcomes: identity- and certification-verified,
  reported in `two_call_cells.csv`, never filtered;
- corrected wall partition required per cell
  (wall_clean + wall_stab = total, 1e-6 s).

**No scientific conclusion is recorded here yet.** The verdict entry is
written only after Codex regenerates `result/b2_full/<stamp>/` from the
transferred raw runs against the verified analysis-code commit, reviews,
and merges (two-commit protocol). A1 and any scale experiment remain out
of scope regardless of the outcome.

## 2026-08-18 — Full-population B2 verdict: current stabilization rejected; focused continuation triggered

**Evidence accepted**: the canonical full-population artifact is
`result/b2_full/20260818T140356Z/`. It joins the certified pilots and
208-cell expansion into exactly 256 matched A2-A5 method-cells: 64
instances per method, including 32 b=0.05 instances per method. All 256
cells certified within the 240-call budget, and all provenance, replay,
solver-status, checkpoint-completeness, wall-partition, and scientific-
setting gates passed.

**Prespecified criteria**:

- acc-1 PASS: A3, A4, and A5 each certified 32/32 b=0.05 instances;
- acc-3 FAIL: median total calls were A2 24, A3 30, A5 32, and A4 34;
  the best stabilized-to-A2 speedup was therefore 24/30 = 0.80, below
  the required 2.0;
- kill-1 ACTIVE: A2 certified 32/32 b=0.05 instances and no stabilized
  method met acc-3;
- kill-3 PASS: every certified convex-hull lower bound remained
  consistent with the paired dictator upper bound (minimum margin 0.01).

**Interpretation**: reject the current A3-A5 implementations as
end-to-end total-oracle-call improvements over plain A2 at n in {8, 12}
and T = 28. Do not summarize this as “stabilization adds nothing.” The
clean-call advantage persisted population-wide: A3, A4, and A5 beat A2
on clean calls on 54/64, 57/64, and 45/64 matched instances,
respectively. The stabilized candidate calls, rather than failure to
accelerate the clean master, prevented amortization.

**Decision**: follow the prespecified continuation branch from the
2026-08-17 decision rule, but only as a new, focused overhead-reduction
study. Its design must be written and reviewed before implementation or
compute, must retain clean-dual certification, and must evaluate on a new
holdout or separately prespecified population rather than tune and claim
success on these 64 instances. The 576-cell A1 campaign and any scale
experiment remain paused and are not implied by this decision.

## 2026-08-18 — A6 continuation SPECIFIED (review pending; no code, no compute)

**Decision**: adopt `doc/A6_SPARSE_STABILIZATION_SPEC.md` as the
prespecification of the focused continuation mandated above, subject to
review of its open questions. Summary of what is frozen there:

- A6 = event-triggered sparse stabilization: seed call + exactly one
  oracle call per subsequent master iteration (clean and candidate calls
  PARTITION the iterations); candidate calls use the A4 Wentges
  mechanism (`a6_a4`, chosen for the most consistent clean-call
  advantage, 57/64, and no stabilized master; the clean RMP solve costs
  LP time but no additional oracle call); clean certification calls fire
  under the FROZEN trigger priority T0 recovery > T4 initialization >
  T3 candidate stall > T1 closable gap (theta_cert = 10*epsilon) >
  T2 staleness (K_MAX = 4) > default candidate. T0 forces clean calls
  through A2's DIRECT escalation/retry logic whenever the previous clean
  call entered ambiguity/refinement/duplicate recovery — candidates
  never interrupt recovery. Certification contract unchanged; skipping
  never affects validity; terminal states are exactly certified,
  budget-exhausted, or fail-loud recovery error.
- Seeds 0-15 are BURNED (motivating/dev only). Holdout FROZEN at exactly
  seeds 16-31 x n {8,12} x b {0.01,0.05} (no seed substitution; any
  infeasible instance halts and amends the preregistration before
  running either method); A2 + the one selected A6 arm = 128 cells.
- Scoring: certified cells score calls-to-certificate; valid
  budget-exhausted cells score 241; both-exhausted pairs tie;
  audit/validity failures halt and are never scored. Adoption requires
  ALL of: >= 61/64 certified, cert rate >= A2's, median score ratio
  <= 0.85, >= 38/64 matched score wins. The decision partition is
  EXHAUSTIVE: adopt / halt-and-debug / final negative (certification
  shortfall, clear kill, gray, or discordant) — every final-negative
  sublabel ends the stabilization line absent new theory.
- Pilot: EXACTLY 24 cells (12 `a6_a4` + 12 `a6_a3` on the burned pilot
  instances); both arms must pass 12/12 implementation audits; `a6_a3`
  is selected only on >= 9/12 score wins (ties non-wins), else `a6_a4`;
  the selection is committed as a machine-readable artifact
  (result/a6_pilot/<stamp>/SELECTION.json) plus a DECISION_LOG entry
  BEFORE any holdout job is generated or submitted.
- All five review questions from the first draft are RESOLVED (spec
  Section 10); nothing about the design remains optional.

**Not decided here**: implementation and launches (follow final spec
review); A1 campaign; scale experiments; the 960-cell grid — all remain
paused.

## 2026-08-19 — A6 burned pilot passed; `a6_a4` selected for the holdout

**Evidence accepted**: the exact 24-cell burned-seed pilot passed its
implementation audit: 24/24 complete, sane, certified, OPTIMAL, and
replay-valid; 12/12 cells passed for each of `a6_a4` and `a6_a3`, with no
budget exhaustion. The canonical machine-readable selection artifact is
`result/a6_pilot/20260819T005514Z/SELECTION.json`, generated by and
attributed to analysis-code commit
`c663fcf5b7a142db595738c8b20bb83549f1ab99`. Its 122 recorded input hashes
match the transferred pilot tree exactly.

**Frozen rule applied**: `a6_a3` had 2 wins in 12 matched pilot instances,
below the prespecified 9/12 threshold (ties are non-wins). Therefore the
single holdout arm is **`a6_a4`**. Descriptively, on this dev-only pilot,
median scores were 23 for `a6_a4` and 32.5 for `a6_a3`; these burned-seed
figures select the mechanism but are not evaluation evidence.

**Decision**: the selection gate is closed and the holdout implementation
may now be built. It must contain exactly fresh A2 plus `a6_a4` on the
frozen seeds 16-31 population specified in
`A6_SPARSE_STABILIZATION_SPEC.md`; `a6_a3` must not appear in the holdout.
No holdout data existed or was inspected before this selection was
committed. A1, the old 960-cell campaign, and scale experiments remain
paused.

## 2026-08-19 — A6 holdout job 218143 halted unscored; full replacement required

**Incident evidence**: the guarded 128-cell holdout launched from commit
`2dba047683e2af48a1ec4d3629dd6e15b20847f5` as Slurm job 218143. Expanded
accounting showed 126 COMPLETED and two FAILED tasks. The failed matched cells
were array index 41 (`a2_s26_n8_b0.05`) and index 105
(`a6_a4_s26_n8_b0.05`); both stopped at their first clean restricted master
with `clean RMP not OPTIMAL: INFEASIBLE`.

**Root cause**: both seed checkpoints contained the identical raw aggregate
load residual `L[7] = -7.356248409800537e-06` kWh, despite the EVSP model's
nonnegative load domain. Extraction had stored the solver's redundant
aggregate `L` values directly rather than reconstructing physical slot load
from nonnegative charge events. With one seed column, the master then required
both `L[7] < 0` and `L[7] >= 0`. The physical instance itself had already
passed the independent constructive feasibility preflight.

**Decision before outcome analysis**: job 218143 is a failed implementation
incident and is never scored. Its 126 completed cells are retained as incident
evidence but will not be mixed with repaired cells. No completed-cell outcome
table or A2/A6 comparison was inspected before this amendment. The repair must
reconstruct physical load from charge events, audit the raw aggregate residual,
use the reconstructed feasible objective for pricing-incumbent upper bounds,
reject malformed master columns before solving, and version the changed
checkpoint identity. After tests and review, the entire same preregistered
128-cell population will be rerun under one new pinned commit. Methods, seeds,
budgets, scoring, and adoption/kill thresholds remain unchanged; there is no
seed substitution and no two-cell-only recovery.

**Scope boundary**: physical-load canonicalization is enabled only inside the
B2/A6 pricing and shared-dictator pipeline. Generic taker extraction and the
legacy Phase 1/boundary replay semantics remain unchanged.
