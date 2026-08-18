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
  immediate-certification outcomes: identity- and certification-verified, reported
  in two_call_cells.csv, never filtered;
- corrected wall partition required per cell
  (wall_clean + wall_stab = total, 1e-6 s).

**No scientific conclusion is recorded here yet.** The verdict entry is
written only after Codex regenerates `result/b2_full/<stamp>/` from the
transferred raw runs against the verified analysis-code commit, reviews,
and merges (two-commit protocol). A1 and any scale experiment remain out
of scope regardless of the outcome.
