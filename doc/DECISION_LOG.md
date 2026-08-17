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

**Decision**: fix the pilot-closeout wall accounting (the first artifact
set mixed wrapper elapsed time into solver-wall fields, so
wall_clean_s + wall_stab_s != total_solver_wall_s) and expose the
clean/stabilized call decomposition in the artifacts; regenerate
artifacts under the corrected code before any further campaign.

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
