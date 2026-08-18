# A6 — event-triggered sparse stabilization: continuation specification

Status: SPECIFICATION ONLY (2026-08-18). No implementation, no launches.
Prespecified before any A6 code exists; constants below are frozen into
the future resume identity. Normative companions:
`B2_STABILIZATION_SPEC.md` (A4 mechanism, certification contract),
`MEASUREMENT_RESULTS.md` Section 8 (bounds), `DECISION_LOG.md` 2026-08-18.

## 1. Motivating evidence (NOT a tuning or evaluation set)

The completed 64-instance full population (`result/b2_full/20260818T140356Z/`,
256/256 certified) established:

| method | median total calls | median clean | median stab | clean W/T/L vs A2 | total W/T/L |
|---|---|---|---|---|---|
| A2 | 24 | 24 | 0 | — | — |
| A3 | 30 | 16 | 14 | 54/5/5 | 8/5/51 |
| A4 | 34 | 18 | 16 | 57/6/1 | 2/7/55 |
| A5 | 32 | 17 | 15 | 45/10/9 | 5/4/55 |

acc-3 failed; kill-1 is active for DENSE stabilization. The decomposition
shows why: stabilized candidates reliably accelerate the clean master
(A4 reduces clean calls on 57/64 instances; A3's clean median is 16 vs
A2's 24), but the DENSE schedule pays one candidate call per iteration, so
totals lose. The overhead is structural, not a defect of the mechanisms:
each dense iteration spends 2 oracle calls where A2 spends 1.

**A6's single purpose: keep the candidate calls' master acceleration
while paying for candidates only when they are likely to matter.** The
64-instance population (seeds 0-15) is hereby BURNED as motivating/dev
evidence: it may inform design and debugging, but no A6 evaluation claim
may cite it.

## 2. Mechanism selection (from the committed tables)

Primary mechanism: **Wentges smoothing (the A4 mechanism)**, because
(i) it has the most CONSISTENT per-instance clean-call advantage
(57/64 — a sparse scheduler fires few candidates, so per-instance
reliability matters more than depth); (ii) it requires NO stabilized
master LP — candidate duals are a convex combination of the stability
center and the CURRENT clean RMP duals, which A6 has for free every
iteration; (iii) it has the smallest constant set (already implemented,
tested, and identity-frozen).

Tightly limited comparison (the only sanctioned one): **sparse-A3**
(du Merle candidates under the same scheduler) may run IN THE PILOT ONLY
(12 burned instances, +12 cells, negligible cost), motivated by A3's
deeper clean reduction (16 vs 18). Prespecified selection rule, applied
once, on burned data only: the holdout arm is sparse-A4 unless sparse-A3
beats sparse-A4 on total calls on >= 9 of the 12 pilot instances, in
which case the holdout arm is sparse-A3. The holdout NEVER runs both.

## 3. A6 mathematics

A6 = A2's certified loop with a SCHEDULER that chooses, each master
iteration, exactly ONE oracle call. Everything below reuses the existing
certified machinery unchanged.

Per master iteration k:

1. Solve the clean RMP over all columns (LP + tangent refinement; NOT an
   oracle call). This yields `UB_k` (exact evaluation — the only UB source,
   unchanged), clean duals `(pi_k, sigma_k)`, and `gap_k = UB_k - LB_best`.
2. Choose the call type `C(k)`:

   CLEAN (certification) iff any trigger fires:
   - **T1 (closable gap)**: `gap_k <= theta_cert` with
     `theta_cert = 10 * epsilon = 0.1` — a certificate plausibly closes,
     so refresh LB now;
   - **T2 (staleness)**: `k_since_clean >= K_MAX = 4` consecutive
     candidate calls since the last clean call — bounds certificate
     staleness and guarantees liveness;
   - **T3 (candidate stall)**: the previous call was a candidate whose
     column was NOT novel — the standard mispricing fallback: the clean
     call both certifies and supplies the Kelley column;
   - **T4 (initialization)**: the first post-seed call is clean
     (initializes LB and the out-point).

   Otherwise CANDIDATE: prices `p_cand = -(alpha * pi_hat +
   (1 - alpha) * pi_k)` — Wentges smoothing toward the CURRENT clean RMP
   dual, with the existing project-prespecified auto-alpha rule,
   Theta_cert serious/null steps, and center updates, all unchanged from
   `B2_STABILIZATION_SPEC.md` Section 2.

3. CLEAN calls update `LB_best` by the unchanged Lasdon formula
   `z_model_k + min(0, pricing_bound - sigma_k)` and flow through A2's
   existing duplicate/exhaustion/deferred-escalation state machine
   verbatim. CANDIDATE calls only add columns and update the smoothing
   state; their `Theta_cert` remains a logged diagnostic, NEVER folded
   into `LB_best`.

**Certification contract (unchanged, and unaffected by skipping):**
`UB_CH` from the clean RMP over all columns every iteration; `LB_CH` only
from clean-dual pricing bounds; certified iff `UB - LB_best <= epsilon =
1e-2`; budget 240 oracle calls, both kinds counted. Skipping a candidate
can never affect validity (candidates only ever ADD columns); skipping a
clean call only DELAYS an LB update, never invalidates one — the
certificate is exactly as valid as A2's, merely refreshed on a schedule.

**Termination**: T2 forces a clean call at least every `K_MAX + 1` calls,
so the clean subsequence is infinite until termination and inherits A2's
finite-termination argument (finite column universe, monotone UB,
bounded escalations, loud failure) unchanged. A6 terminates certified or
budget-exhausted.

**Expected budget arithmetic (motivation, not a prediction):** dense A4
needed ~16-18 master iterations (its clean-call median) at 2 calls each.
A6 spends ~1 call per iteration plus extra clean refreshes
(~1 per K_MAX+T1/T3 events). If the candidate quality transfers, totals
land near iterations + refreshes ≈ high teens vs A2's 24 — a 15-30%
reduction is the plausible range, and the acceptance bar (Section 6) is
set accordingly BELOW the old (rejected) 2x bar, because the continuation
claim is "stabilization can pay for itself," not "stabilization is 2x."

## 4. Prespecified constants (frozen; all enter the resume identity)

| constant | value | role |
|---|---|---|
| `theta_cert` | `10 * epsilon = 0.1` | T1 gap trigger |
| `K_MAX` | 4 | T2 max consecutive candidates |
| alpha machinery | unchanged A4 constants (`alpha0 0.5`, decr 0.1, incr frac 0.1, cap 0.99) | candidate smoothing |
| `epsilon`, budget, `pwl_tol`, `rc_tol`, `tol_d` | unchanged (1e-2, 240, 1e-3, 1e-6, 1e-2) | contract |

These are round-number conventions chosen WITHOUT optimization on seeds
0-15. If the pilot motivates changing any of them, that change is a new
prespecification and the holdout remains untouched until the final
configuration is frozen.

## 5. Logging and checkpoint identity (prespecified)

- identity adds: `method: "a6"` (or `"a6b"` for sparse-A3),
  `scheduler: {theta_cert: 0.1, k_max: 4, triggers: [T1, T2, T3, T4]}`,
  plus the unchanged mechanism constants;
- every oracle event records `call_kind` in {seed, clean, candidate} and
  `trigger_reason` in {T1, T2, T3, T4, default-candidate};
- iteration events record `gap_at_decision`, `k_since_clean`, and the
  scheduler decision, alongside the existing evidence contract (solve
  ids, bounds, replay, walls);
- checkpoint state adds the scheduler counters so resume reproduces the
  identical decision sequence (same preemption tests as A2-A5: identical
  nonvolatile record stream after interruption at any boundary);
- audit: existing cg gates apply; additionally every clean gap between
  consecutive clean calls must be <= K_MAX candidates (audit-checkable
  from trigger_reason sequences).

## 6. Holdout population, endpoints, decision thresholds (prespecified)

**Holdout**: seeds 16-31 x n {8, 12} x b {0.01, 0.05} = 64 NEW instances,
disjoint from the burned 0-15 population by construction. Feasibility
screen (before freezing the holdout): one taker solve per instance at
posted prices; if any instance is infeasible, substitute the next unused
seed (32, 33, ...) in increasing order and record the substitution in the
campaign manifest. Methods on the holdout: **A2 and the single A6 arm
only** (64 matched pairs, 128 method-cells) — A3-A5 dense results on new
seeds would add 192 cells with no decision value, and A2 must be run
fresh because its seeds 0-15 statistics do not transfer.

**Primary endpoint**: median total oracle calls to certificate, matched
A6 vs A2 on the 64 holdout instances. Also reported: clean calls,
candidate (stabilized) calls, solver wall time (corrected partition),
certification rate, final gaps, serious/null steps, trigger-reason
counts, matched W/T/L on totals and on clean calls, uplift intervals.

**Acceptance (adopt A6)** — ALL must hold on the holdout:
- `acc-A6-1`: A6 certifies >= 61/64 (95%) within 240 calls;
- `acc-A6-2` (primary): `median(A6 total) / median(A2 total) <= 0.85`
  AND A6 wins >= 38/64 matched instances on total calls (ties are
  non-wins); supporting inference: two-sided sign test on non-tied pairs
  at alpha = 0.05 (reported, not gating);
- `acc-A6-3`: A6 certification rate >= A2's on the same holdout.

**Kill (terminate the stabilization line permanently)**:
- `kill-A6-1`: median ratio >= 1.0 OR wins <= 32/64;
- gray zone (0.85 < ratio < 1.0 and wins > 32): NOT adopted; recorded as
  a negative result with nuance; no further stabilization variants
  without new theory (this outcome is prespecified as final);
- `kill-A6-2` (guardrails): any certification-validity violation halts
  (halt-and-debug); audit gates as in Section 5.

## 7. Bounded pilot (before the holdout campaign)

- Cells: A6 on the 12 BURNED pilot instances (seeds {0, 11, 15} x
  n {8, 12} x b {0.01, 0.05}); optionally +12 sparse-A3 cells under the
  Section 2 selection rule. A2 baselines on these instances already
  exist and are not re-run.
- Gates (implementation, not evaluation): 12/12 complete and sane;
  bound sanity and audit (cg=12 per arm); determinism and preemption
  batteries pass locally; trigger accounting consistent (clean-call
  spacing <= K_MAX + 1); call counts within [2, 240].
- The pilot may NOT adjust constants silently (Section 4 rule) and its
  results may not be cited as evaluation evidence.

## 8. Estimated Unicorn cost

From the 208-cell expansion (one overnight at %12, ~2-5 min median per
cell all-in): pilot 12-24 cells ≈ well under 1 hour; holdout 128 cells ≈
half an expansion night, ~3-6 hours wall at %12 with requeue-safe
checkpoints. Total: one short evening (pilot + review) plus one overnight
(holdout). No new cluster resources needed (4 CPU / 8 GB / 24 h per task
unchanged).

## 9. Out of scope (this continuation)

The A1 tatonnement campaign (576 cells), any scale experiment (larger n,
more slots, multiple fleets, coupling rows), stabilized-Theta_cert
certification variants, and the 960-cell grid all remain out of scope and
paused. Implementation itself follows only after this specification is
reviewed and its open questions (below) are resolved.

## 10. Open review questions

1. Single holdout arm with the pilot-gated A3/A4 selection rule
   (Section 2) — or drop sparse-A3 entirely and commit to sparse-A4 now?
2. Are `theta_cert = 10 * epsilon` and `K_MAX = 4` acceptable as frozen
   round-number conventions, or should a different convention be fixed
   before implementation?
3. Is the acceptance bar (>= 15% median reduction AND >= 38/64 wins) the
   right ambition level for adopting A6 into the thesis narrative?
4. Holdout = A2 + one A6 arm only (128 cells): agreed, or should any
   dense method be re-run on the holdout for continuity?
5. Pilot on burned seeds {0, 11, 15}: agreed that this is dev-only and
   uncitable?
