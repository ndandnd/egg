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

Primary mechanism: **Wentges smoothing (the A4 mechanism)**, method
identity **`a6_a4`**, because (i) it has the most CONSISTENT per-instance
clean-call advantage (57/64 — a sparse scheduler fires few candidates, so
per-instance reliability matters more than depth); (ii) it requires NO
stabilized master LP — candidate duals are a convex combination of the
stability center and the CURRENT clean RMP duals, which A6 already holds
each iteration (the clean RMP solve costs LP time but NO additional
oracle call); (iii) it has the smallest constant set (already
implemented, tested, and identity-frozen).

Tightly limited comparison (the only sanctioned one): **`a6_a3`**
(du Merle candidates under the same scheduler) runs IN THE PILOT ONLY,
motivated by A3's deeper clean reduction (16 vs 18). The pilot is exactly
24 cells (Section 7) and its one-shot selection rule decides the single
holdout arm. The holdout NEVER runs both.

## 3. A6 mathematics

A6 = A2's certified loop with a SCHEDULER that chooses, each master
iteration, exactly ONE oracle call. Everything below reuses the existing
certified machinery unchanged, EXCEPT the recovery semantics (T0), which
replace the dense deferred-escalation state machine for sparse
scheduling.

Per master iteration k:

1. Solve the clean RMP over all columns (LP + tangent refinement; this
   costs LP wall time but NO ADDITIONAL ORACLE CALL). This yields `UB_k`
   (exact evaluation — the only UB source, unchanged), clean duals
   `(pi_k, sigma_k)`, and `gap_k = UB_k - LB_best`.
2. Evaluate ALL triggers, record every trigger that fires AND the one
   selected under the FROZEN DETERMINISTIC PRIORITY

       T0 recovery > T4 initialization > T3 candidate stall >
       T1 closable gap > T2 staleness > default candidate,

   then make the selected call:

   - **T0 (safety/recovery, highest priority)**: the previous clean call
     entered a recovery path — ambiguous pricing (incumbent rc not
     materially negative while the certified rc bound is `< -rc_tol`),
     certified-exhaustion PWL refinement, or duplicate-negative-
     reduced-cost retry. The next call is FORCED CLEAN and A2's DIRECT
     escalation/retry logic applies on the clean subsequence (tighten
     `pricing_max_mip_gap` /100 on ambiguity, tangent refinement on
     exhaustion, bounded retries with loud failure — the ORIGINAL A2
     branches, not the dense candidate-mediated deferral, which is
     specific to the dense schedule and is NOT reused in A6). Candidate
     calls must never interrupt a recovery sequence: T0 keeps firing
     until the recovery resolves (novel improving column, certificate,
     or loud failure).
   - **T4 (initialization)**: the first post-seed call is clean
     (initializes LB and the out-point).
   - **T3 (candidate stall)**: the previous call was a candidate whose
     column was NOT novel — the standard mispricing fallback: the clean
     call both certifies and supplies the Kelley column.
   - **T1 (closable gap)**: `gap_k <= theta_cert` with
     `theta_cert = 10 * epsilon = 0.1` — a certificate plausibly closes,
     so refresh LB now.
   - **T2 (staleness)**: `k_since_clean >= K_MAX = 4` consecutive
     candidate calls since the last clean call — bounds certificate
     staleness and guarantees repeated certification opportunities.
   - **default CANDIDATE**: prices `p_cand = -(alpha * pi_hat +
     (1 - alpha) * pi_k)` — Wentges smoothing toward the CURRENT clean
     RMP dual (`a6_a4`; du Merle candidate duals for `a6_a3`), with the
     existing project-prespecified auto-alpha rule, Theta_cert
     serious/null steps, and center updates, all unchanged from
     `B2_STABILIZATION_SPEC.md`.

3. CLEAN calls update `LB_best` by the unchanged Lasdon formula
   `z_model_k + min(0, pricing_bound - sigma_k)`. CANDIDATE calls only
   add columns and update the smoothing state; their `Theta_cert`
   remains a logged diagnostic, NEVER folded into `LB_best`.

**Certification contract (unchanged, and unaffected by skipping):**
`UB_CH` from the clean RMP over all columns every iteration; `LB_CH` only
from clean-dual pricing bounds; certified iff `UB - LB_best <= epsilon =
1e-2`; budget 240 oracle calls, both kinds counted. Skipping a candidate
can never affect validity (candidates only ever ADD columns); skipping a
clean call only DELAYS an LB update, never invalidates one — the
certificate is exactly as valid as A2's, merely refreshed on a schedule.

**Termination and terminal states**: T2 guarantees REPEATED clean
certification opportunities (a clean call at least every `K_MAX + 1`
calls outside recovery; more often inside T0), and under the finite-
column assumptions the clean subsequence retains A2's progress
machinery. The actual terminal states are exactly: CERTIFIED,
BUDGET-EXHAUSTED (valid completed outcome), or FAIL-LOUD RECOVERY ERROR
(bounded retries exceeded). No unconditional finite-termination claim is
made beyond these three states; the budget is the hard stop.

**Expected budget arithmetic (motivation, not a prediction):** A6 spends
exactly `1 (seed) + 1 oracle call per subsequent master iteration`.
Clean refreshes PARTITION those iterations between clean and candidate
calls — they are not extra calls added on top of an iteration count.
The relevant unknowns are (i) how many master iterations the sparse
candidate stream needs to assemble the certifying column set (dense-A4
evidence: its master ran ~16-18 iterations, but each dense iteration
injected BOTH a candidate and a Kelley column, so the sparse iteration
count may be somewhat higher), and (ii) how many additional iterations
delayed certification detection costs (LB refreshes only at clean
calls). If those two effects stay moderate, totals land in the high
teens to low twenties vs A2's 24 — which is why the acceptance bar
(Section 6) is set at a 15% median reduction, deliberately BELOW the old
(rejected) 2x bar: the continuation claim is "stabilization can pay for
itself," not "stabilization is 2x."

## 4. Prespecified constants (frozen; all enter the resume identity)

| constant | value | role |
|---|---|---|
| `theta_cert` | `10 * epsilon = 0.1` | T1 gap trigger |
| `K_MAX` | 4 | T2 max consecutive candidates |
| trigger priority | `T0 > T4 > T3 > T1 > T2 > default` | frozen deterministic selection |
| T0 recovery constants | A2's existing escalation constants unchanged (gap /100 floor 1e-12; MAX_PRICING_ESCALATIONS 4; MAX_DUPLICATE_RETRIES 3) | recovery |
| alpha machinery | unchanged A4 constants (`alpha0 0.5`, decr 0.1, incr frac 0.1, cap 0.99) | candidate smoothing (`a6_a4`) |
| du Merle machinery | unchanged A3 constants | candidate master (`a6_a3` only) |
| `epsilon`, budget, `pwl_tol`, `rc_tol`, `tol_d` | unchanged (1e-2, 240, 1e-3, 1e-6, 1e-2) | contract |

These are round-number conventions chosen WITHOUT optimization on seeds
0-15. If the pilot motivates changing any of them, that change is a new
prespecification and the holdout remains untouched until the final
configuration is frozen.

## 5. Logging and checkpoint identity (prespecified)

- identity adds: `method: "a6_a4"` (or `"a6_a3"`),
  `scheduler: {theta_cert: 0.1, k_max: 4,
  priority: [T0, T4, T3, T1, T2, default]}`, plus the unchanged
  mechanism constants;
- every oracle event records `call_kind` in {seed, clean, candidate},
  `triggers_fired` (the full list of triggers that evaluated true), and
  `trigger_selected` in {T0, T1, T2, T3, T4, default-candidate} (the one
  chosen under the frozen priority);
- iteration events record `gap_at_decision`, `k_since_clean`, the
  recovery-state flag driving T0, and the scheduler decision, alongside
  the existing evidence contract (solve ids, bounds, replay, walls);
- checkpoint state adds the scheduler counters and recovery state so
  resume reproduces the identical decision sequence (same preemption
  tests as A2-A5: identical nonvolatile record stream after interruption
  at any boundary);
- audit: existing cg gates apply; additionally (i) every gap between
  consecutive clean calls must be <= K_MAX candidates outside recovery,
  (ii) every T0-flagged iteration must be a clean call, and (iii) no
  candidate call may appear while the recovery flag is set — all
  checkable from the committed trigger fields.

## 6. Holdout population, endpoints, decision thresholds (prespecified)

**Holdout — FROZEN**: exactly seeds 16-31 x n {8, 12} x b {0.01, 0.05}
= 64 instances, disjoint from the burned 0-15 population by construction.
NO adaptive seed substitution. If any generated instance turns out
infeasible, HALT before running either method on the holdout and amend
this preregistration explicitly; observations are never replaced.
Methods on the holdout: **A2 and the single selected A6 arm only**
(64 matched pairs, 128 method-cells) — A3-A5 dense results on new seeds
would add 192 cells with no decision value, and A2 must be run fresh
because its seeds 0-15 statistics do not transfer.

**Scoring (prespecified; used for every W/T/L and median-ratio
computation):**
- raw oracle-call counts are always recorded as the actual counts;
- a CERTIFIED cell scores its calls-to-certificate;
- a VALID budget-exhausted cell scores **241** (budget + 1);
- if both methods of a matched pair are budget-exhausted, the pair is a
  TIE;
- audit or certification-validity failures are NEVER scored: they HALT
  the campaign (halt-and-debug), and no conclusion is drawn.

**Primary endpoint**: median SCORE (as defined above), matched A6 vs A2
on the 64 holdout instances. Also reported: raw calls, clean calls,
candidate calls, solver wall time (corrected partition), certification
rate, final gaps, serious/null steps, trigger-selected counts, matched
W/T/L on scores and on clean calls, uplift intervals.

**Decision partition (exhaustive; every valid campaign lands in exactly
one cell).** Let `ratio = median(A6 score) / median(A2 score)`, `W` = A6
matched wins on scores (ties non-wins), and let the certification gates
be `acc-A6-1`: A6 certifies >= 61/64, and `acc-A6-3`: A6 certification
rate >= A2's on the holdout.

0. **HALT-AND-DEBUG** (no conclusion): any audit or certification-
   validity violation in either method's cells. Never scored.
1. **ADOPT**: acc-A6-1 AND acc-A6-3 AND `ratio <= 0.85` AND `W >= 38`.
   (Supporting inference, reported not gating: two-sided sign test on
   non-tied score pairs at alpha = 0.05.)
2. **FINAL NEGATIVE — certification shortfall**: acc-A6-1 or acc-A6-3
   fails, regardless of speed results.
3. **FINAL NEGATIVE — clear kill**: certification gates pass and
   (`ratio >= 1.0` OR `W <= 32`).
4. **FINAL NEGATIVE — gray**: certification gates pass and
   `0.85 < ratio < 1.0` and `W >= 33`.
5. **FINAL NEGATIVE — discordant**: certification gates pass and either
   (`ratio <= 0.85` with `33 <= W <= 37`: the median moves but the
   effect is concentrated in a subset of instances) or
   (`W >= 38` with `0.85 < ratio < 1.0`: many small wins without the
   required median effect).

Exhaustiveness check (given certification gates pass): ratio falls in
{<= 0.85, (0.85, 1.0), >= 1.0} and W in {<= 32, 33-37, >= 38}; case 1
covers (<= 0.85, >= 38); case 3 covers all of ratio >= 1.0 and all of
W <= 32; cases 4-5 cover the remaining four combinations. EVERY
final-negative sublabel carries the same consequence: no further
stabilization variants without new theory. ADOPT is the only outcome
that continues the stabilization line.

## 7. Bounded pilot (before the holdout campaign)

- Cells: EXACTLY 24 — `a6_a4` AND `a6_a3` on the 12 BURNED pilot
  instances each (seeds {0, 11, 15} x n {8, 12} x b {0.01, 0.05}). A2
  baselines on these instances already exist and are not re-run.
- Gates (implementation, not evaluation): BOTH arms must pass 12/12
  implementation audits — complete and sane, bound sanity, cg=12 per
  arm, determinism and preemption batteries locally, trigger accounting
  consistent (clean-call spacing <= K_MAX + 1 outside recovery; T0
  iterations clean; no candidate inside recovery), call counts within
  [2, 240].
- **One-shot arm selection (on burned data, applied once)**: select
  `a6_a3` for the holdout iff it beats `a6_a4` on the total-call SCORE
  (Section 6 scoring) on AT LEAST 9 of the 12 pilot instances, ties
  counted as non-wins; otherwise select `a6_a4`.
- **Selection artifact (machine-readable, committed BEFORE any holdout
  job is generated or submitted)**: `result/a6_pilot/<stamp>/SELECTION.json`
  containing the per-instance scores of both arms, the win count, the
  applied rule, the selected method identity, the analysis-code commit,
  and hashes of the pilot inputs; plus the arm decision recorded in
  DECISION_LOG.md. NO holdout data may be generated, submitted, or
  inspected before this artifact is committed.
- The pilot may NOT adjust constants silently (Section 4 rule) and its
  results may not be cited as evaluation evidence.

## 8. Estimated Unicorn cost

From the 208-cell expansion (one overnight at %12, ~2-5 min median per
cell all-in): pilot exactly 24 cells ≈ well under 1 hour; holdout 128
cells ≈ half an expansion night, ~3-6 hours wall at %12 with requeue-safe
checkpoints. Total: one short evening (pilot + selection commit + review)
plus one overnight (holdout). No new cluster resources needed
(4 CPU / 8 GB / 24 h per task unchanged).

## 9. Out of scope (this continuation)

The A1 tatonnement campaign (576 cells), any scale experiment (larger n,
more slots, multiple fleets, coupling rows), stabilized-Theta_cert
certification variants, and the 960-cell grid all remain out of scope and
paused. Implementation itself follows only after this specification is
reviewed and its open questions (below) are resolved.

## 10. Resolved review decisions (2026-08-18)

All five open questions from the first draft were resolved in review;
none remains optional:

1. **Pilot arms**: the pilot is EXACTLY 24 cells (12 `a6_a4` + 12
   `a6_a3`); both arms must pass 12/12 implementation audits; the
   one-shot >= 9/12 score rule (ties non-wins) selects the single
   holdout arm, default `a6_a4`; the selection is committed as a
   machine-readable artifact before any holdout work (Section 7).
2. **Constants**: `theta_cert = 10 * epsilon` and `K_MAX = 4` are
   APPROVED as frozen round-number conventions, joined by the frozen
   trigger priority `T0 > T4 > T3 > T1 > T2 > default` (Section 3).
3. **Adoption bar**: APPROVED at ratio <= 0.85 AND >= 38/64 wins, with
   the budget-exhaustion scoring rule (score 241) and the exhaustive
   decision partition of Section 6.
4. **Holdout arms**: APPROVED as A2 + one selected A6 arm only
   (128 method-cells); dense methods are not re-run.
5. **Burned pilot**: APPROVED — seeds 0-15 (including the pilot's
   {0, 11, 15}) are dev-only and uncitable as evaluation evidence.
