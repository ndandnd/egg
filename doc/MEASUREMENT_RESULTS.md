# Measurement results: certified synthetic closeout

Date: 2026-08-16. Status: definitive analysis of the certified measurement
campaigns. Analysis code: `src/experiments/analyze_closeout.py` (tested in
`src/tests/test_analysis.py`); generated tables and figures:
`result/analysis/20260816T190835Z/` (its `MANIFEST.json` names the analysis code
commit ce2fa5c and carries SHA-256 hashes of every canonical input and every
generated output; integrity is test-enforced). Canonical immutable inputs:
`result/{phase1,damping_frontier,boundary_fine}/20260816T180507Z/` and
`result/RESULTS_OVERVIEW_20260816T180507Z.md`.

Certification: every number below is computed from records with
`replay_effective_ok = True` and `solver_status = OPTIMAL`, cross-validated
against the run checkpoints and the audited SUMMARY.md files (the analysis
aborts on any disagreement; none occurred). Raw replay information is never
hidden: Phase 1 carries 18 raw legacy replay failures and the damping
frontier 163, all revalidated `certified_equivalent` with zero unresolved
(table `T8_audit_totals.csv`).

Scope caveat, stated up front: **all findings are certified properties of the
synthetic laboratory** (two-terminal/one-depot instances, 60 kWh batteries,
duck-shaped affine price impact p_t = a_t + b_t(U_t + L_t)); none is yet an
external-validity claim. See "Limitations".

## 1. The taker iteration: fixed points, cycles, unresolved transients

Tables `T1_loop_cells.csv`, `T1b_outcome_rates.csv`; figure
`F1_outcome_rates.png`. 416 loop cells total (Phase 1: 128; damping frontier:
288), classified by state-correct detection (fixed point requires the price
state to reproduce itself within 1e-4; a cycle requires exact price-state
recurrence at lag >= 2; `max_iters` is an **unresolved transient — never
convergence**; median final price residual among max_iters cells is 0.095,
three orders of magnitude above tolerance).

Headline rates:

- **b = 0 (no feedback):** 32/32 cells reach the trivial fixed point in one
  iteration — the price-taker limit behaves exactly as EVSP-DR assumes.
- **b = 0.002 (weak feedback):** 62.5–75% fixed points; the rest are
  certified cycles. Weak feedback is *mostly* stable, and damping can rescue
  it: seed 0 / n=12 flips from a certified 2-cycle (alpha >= 0.25) to a
  fixed point at alpha = 0.1 — the single damping-induced rescue in the
  campaign.
- **b = 0.01 (moderate):** fixed-point rate collapses to 1/8 (Phase 1) and
  1/16 (damping) at *every* damping level; cycles dominate (87.5–93.75% at
  alpha >= 0.2).
- **b = 0.05 (strong):** **zero fixed points in all 176 cells across nine
  damping levels.** At alpha = 1: 24/24 cycles. At alpha = 0.05: 16/16
  unresolved transients.

**For b in {0.01, 0.05}, damping does not create convergence; it trades
short certified cycles for long orbits and unresolved transients.** (At
b = 0.002 the single seed-0/n=12 rescue above shows weak feedback can be
stabilized by constant damping.) Median iterations-to-outcome scale like
1/alpha (4 at alpha=1 to 240 at alpha=0.05). This is the central negative
result motivating B2: at moderate-to-strong feedback, naive constant-damping
tatonnement is not a reliable coordination algorithm for an indivisible
fleet, at any tested damping level.

## 2. Cycle structure

Table `T2_cycle_lengths.csv`; figure `F2_cycle_lengths.png`. 284 certified
cycles.

- **Every undamped (alpha = 1) cycle observed has length exactly 2** —
  49/49, a certified empirical pattern of this laboratory (not a proven
  universal). The pure cobweb: the fleet flip-flops between two schedules
  straddling a kink of its value function.
- **Damped cycles are long-period**: median length 11 (b=0.01) and 14
  (b=0.05) in the damping frontier, maximum 140. Damping smears the 2-cycle
  into long closed orbits in price space rather than collapsing it.
- 228 of 284 cycles (80%) have length > 2. Cycle-length detection is capped
  by the 240-iteration budget, so some `max_iters` cells may be longer-period
  orbits — another reason they are labeled unresolved rather than divergent.

## 3. Seed and instance heterogeneity

Table `T4_outcomes_by_seed.csv`. Stability is **strongly
instance-dependent within this generator and the tested constant-damping
family**: in the damping frontier, seed 11 accounts for *all nine*
fixed-point cells at b = 0.01 (one per damping level), while the other 15
seeds produce zero fixed points at any alpha. Phase 1 shows the same pattern
at smaller scale (its b>0 fixed points concentrate in specific seed/size
pairs, with the one seed-0/n=12 damping rescue at b = 0.002). Within the
tested family, whether an instance admits a stable point appears decided
largely by the geometry of its schedule set relative to the price curve
rather than by the damping parameter — relevant to theorem target B10
(fixed-point existence tied to integrality structure), pending tests beyond
this generator and beyond constant damping.

## 4. Runtime and LP/MIP gaps

Table `T5_solver_stats.csv`; figure `F5_solver_stats.png`. All **49,993
recorded solves** GRB/OPTIMAL. Median MIP wall times are small (1.1–2.1 s
for statics/sweeps; 19.8 s for damping-frontier iterations) with heavy tails
(p90 up to 171 s, max 543 s) — consistent with kink-adjacent instances being
much harder. Root-LP-to-MIP absolute gaps are large: medians 127.4 (Phase 1
overall), 301.3 (damping iterations), 84.8 (boundary), maxima up to 700.
**These are formulation-specific integrality-gap measurements** — root-LP
gaps of the compact vehicle-indexed MILP — and they motivate, but do not
measure, the convex-hull uplift that B3 defines on the schedule-column
master (z_D − z_CH, Section 8). They must not be read as the intrinsic
"price of indivisibility" of the instances.

## 5. Static-regime welfare ladder

Tables `T6_welfare_ladder.csv`, `T6b_welfare_gaps.csv`,
`T6c_welfare_gap_summary.csv`; figure `F3_welfare_gaps.png`. 32 instance
cells x 4 regimes x 4 independent solver draws. Own-objective
alpha-invariance validated for taker/strategic/dictator; the four draws
expose selection variance only through *cross-lens* metrics (next
subsection). Mean (max) total-system cost gaps versus the dictator:

| b | uncontrolled − dictator | taker − dictator | strategic − dictator |
|---|---|---|---|
| 0 | 22.2 (62.2) | 0 (0) | 0 (0) |
| 0.002 | 22.9 (60.5) | 0.08 (0.33) | 0.09 (0.23) |
| 0.01 | 22.7 (60.2) | 2.45 (8.33) | 0.56 (1.25) |
| 0.05 | 40.8 (82.6) | **25.97 (79.8)** | 1.12 (3.74) |

Two certified findings:

1. **The price-taker's self-defeating cost grows steeply with price impact**:
   from exactly zero at b=0 to a mean of 26 (max 80) at b=0.05 — approaching
   the uncontrolled fleet's worst cases (max 82.6). Naive price-following
   under strong feedback forfeits most of the value of optimization; the
   B8 conjecture (W_T can approach or exceed W_U) is within reach of this
   laboratory at the worst-case level, though not yet in the mean.
2. **The strategist nearly implements the planner**: strategic − dictator
   stays ≤ 3.74 across the whole grid. At strong feedback (b = 0.05) in this
   laboratory, the monopsony distortion (B9) is an order of magnitude smaller
   than the price-taking distortion — anticipating one's own price impact
   recovers almost all coordination value even without a market designer. At
   weaker slopes both distortions are small and the comparison is not yet
   informative.

### Degeneracy diagnostic (selection variance)

Repeated identical solves differ only via optimizer tie-breaking. Across 128
regime-cells, exactly one shows material cross-lens selection spread:
an `uncontrolled` cell at b=0 with spread 12.8 in total-system cost (the
flat-price EVSP has degenerate optima whose charge-on-arrival re-timings land
in different duck-price hours). Taker spread: 0; dictator: ≤ 0.0009;
strategic: ≤ 0.0065. Alternative-optima selection is a real but presently
small phenomenon — it must stay measured because B2's stabilized masters will
interact with exactly this degeneracy.

## 6. Boundary switches: the discontinuous response, economically filtered

Tables `T7_switches.csv`, `T7b_switches_by_cell.csv`,
`T7c_switch_summary.csv`; figure `F4_switch_jumps.png`. 64 fine sweeps
(delta grid 0.01) produced 2,740 adjacent-pair response changes, of which:

- **2,559 degenerate ties** (hash flips with no material load change) —
  excluded from the economic count;
- **89 margin-tied events** — schedule swaps where cross-realization
  margins are ~0 (the margin test re-prices schedule B's trip partition at
  A's prices via the fixed-sequence oracle): alternative optima exactly at
  the boundary, also excluded. This is the margin test doing precisely its
  job: 89 would-be "switches" are certified as economically meaningless.
- **92 economic switches in 43 of 64 cells**: 57 duty changes, 35
  charging-only, 0 fleet changes.

Load-jump distribution (economic switches): median L1 jump 35.5 kWh, maximum
195.8 kWh — a fifth of a small depot's daily energy moving discontinuously
under a 0.01-currency price perturbation. By trip count: n=8 median 35.4
(max 89.2, 33 switches); n=12 median 36.6 (max 195.8, 59 switches) — larger
instances switch more often and more violently. By perturbed slot: midday
slot 12 has the largest median jump (49.5 kWh, 32 switches); evening slot 20
the smallest (28.2, 10 switches).

Interpretation for the direction decision (handoff gate 8.7): **duty changes
outnumber charging-only changes 57:35** — the discontinuity is substantially
a routing/partition phenomenon, not merely charge-timing. This keeps the
atomic/switch-boundary program (and eventually B31) alive, while the 2,559:92
degenerate-to-economic ratio warns that any learning on raw schedule hashes
without economic filtering would be fitting alternative-optimum selection —
which schedule the solver reports among economically equivalent optima —
rather than economic structure.

## 7. Limitations

1. **Synthetic laboratory.** Two terminals, one depot, 6–12 trips, uniform
   physics, affine duck-shaped price impact with constant base load. No
   charger contention, no network, no V2G, no reserve products.
2. **Instance family bias.** One generator; heterogeneity findings (seed 11)
   show instance structure matters, so generator-specific artifacts cannot be
   excluded.
3. **Budget-capped classification.** `max_iters` cells (66/416) are
   unresolved; some may be longer-period cycles.
4. **Cross-lens welfare under degeneracy** is selection-dependent (measured,
   small, but present).
5. **Real data pending.** The frozen GIRO subset (trips, deadheads, physics
   per `ref/context/GIRO_DATASET_HANDOFF_20260814.md`) has not yet been
   delivered; every claim here is pre-external-validity.

## 8. B2 experimental design: stabilized price negotiation

Goal: replace the demonstrably unreliable damped tatonnement with stabilized
Dantzig-Wolfe price coordination on the dictator problem, with certificates,
and quantify the improvement against the unchanged baselines above. This PR
specifies the design only; no B2 code is included.

### Algorithms

All operate on the same master: schedule-columns (complete taker solutions:
load vector + operating cost) with convexity row, plus the convex PWL system
cost of U+L; duals of the load-balance rows are the posted prices; the
column oracle is the existing taker EVSP at those prices (unchanged, so all
existing certification applies).

- **A0 (baseline)**: undamped tatonnement — the certified 2-cycle machine.
- **A1 (baseline)**: damped tatonnement at the empirically best fixed alpha
  per b from `T1b_outcome_rates.csv`.
- **A2**: pure (unstabilized) column generation on the master — Kelley; adds
  memory of all past responses but no stabilization.
- **A3**: du Merle box + linear-penalty stabilization (5-piece), stability
  center updated on serious steps.
- **A4**: Wentges dual smoothing with the Pessoa et al. auto-parameter rule.
- **A5**: quadratic proximal stabilization (bundle-style; parameter halved on
  null steps).

### Bounds and certification (definitions)

For each instance, minimization throughout:

- `z_D`   = integer dictator optimum. Available per instance from the
  existing adaptive dictator solve as a certified interval
  `[z_D_ub - tol_D, z_D_ub]` with `tol_D = 1e-2` (`obj_true` is the feasible
  upper bound).
- `z_CH`  = optimum of the FULL schedule-column convex-hull master (all
  feasible schedule columns) — never computed directly.
- `z_RMP` = optimum of the restricted master over the columns generated so
  far. Fewer columns can only hurt a minimization, so
  **`z_RMP >= z_CH`: the restricted master is the upper bound `UB_CH`.**
- `LB_CH` = lower bound on `z_CH` from exact pricing reduced-cost accounting
  (Lasdon bound: `z_RMP` plus the convexity-row-weighted minimum reduced
  cost returned by the exact oracle).

**Certification** for CG-based methods (A2–A5): `UB_CH - LB_CH <= epsilon`
with `epsilon = 1e-2`. This certifies `z_CH`, not `z_D`.

**B3 uplift** is `z_D - z_CH`, reported as a certified interval that carries
both tolerances: `[(z_D_ub - tol_D) - UB_CH, z_D_ub - LB_CH]`.

The quantity "integer restricted-master value minus `z_RMP`" is the
**restricted-menu integrality gap**; it may be reported as a diagnostic but
must NOT be called uplift unless pricing completeness (or an equivalent
argument) establishes both `z_RMP = z_CH` and that the integer restricted
master attains `z_D`.

A0/A1 (tatonnement) carry **no CG certificate** — they produce no valid
bound on `z_CH` — so calls-to-certificate comparisons are restricted to
A2–A5; A0/A1 are compared at matched oracle budgets on outcome metrics.

### Metrics (per cell, all logged under the Phase-0 record contract)

1. A2–A5 only: oracle calls and wall time to `UB_CH - LB_CH <= epsilon`;
   final certified gap; `UB_CH`, `LB_CH` trajectories.
2. B3 uplift interval per instance (by-product of 1 plus the existing
   dictator solve), with tolerance accounting as defined above.
3. All methods: price-path quality — L-infinity step sizes and total
   variation of the dual/posted-price trajectory.
4. A0/A1 at matched oracle budgets (the budget at which each certified
   method terminated, and the full 240-call budget): fixed-point success,
   final price residual, realized welfare (total system cost of the final
   and of the time-averaged response), price-path total variation, wall
   time.
5. Replay validity and OPTIMAL status for every oracle call (unchanged
   gates); restricted-menu integrality gap as a labeled diagnostic.

### Acceptance tests

- On the 176 cells where b = 0.05 (zero fixed points today), A3/A4/A5 reach
  the epsilon-certificate within 240 oracle calls in >= 95% of cells.
- Bound sanity on every cell: `LB_CH <= UB_CH` at every iteration; `UB_CH`
  is nonincreasing at serious steps; the certified `z_CH` interval is
  consistent with the dictator interval (`z_CH <= z_D_ub + numerical
  tolerance`).
- Among CG methods: the best stabilized method (A3–A5) beats plain CG (A2)
  by >= 2x on median oracle calls to certificate at b in {0.01, 0.05}.
- Budget-matched superiority over tatonnement: at each certified method's
  termination budget, A0/A1 fail to reach a price residual below tol_price
  on the cells where they cycle today, and the stabilized methods' price-path
  total variation is below A0/A1 on >= 90% of cells.
- Determinism: rerunning any cell reproduces its record stream.

### Kill tests

- If A2 (plain CG, no stabilization) already meets the acceptance bar,
  stabilization is not the contribution — the story collapses to "memory
  beats memorylessness" and Chapter I's algorithmic half must be re-scoped
  to the equivalence theorem plus uplift accounting.
- If A1 (best fixed damping), compared at matched oracle budgets, matches
  the certified methods on realized welfare and reaches residuals below
  tol_price on a comparable fraction of cells across the full b grid, then
  stabilized negotiation adds nothing practical here; retain only the theory
  link. (A1 cannot match on certificates, which it does not produce; the
  comparison is on outcomes.)
- If the certified `z_CH` interval ever contradicts the dictator interval
  (`LB_CH > z_D_ub + tolerance`), the decomposition identity implementation
  is wrong — halt and debug before any scientific claim.

### Proposed Unicorn grid

Seeds 0–15; n_trips {8, 12}; b {0.002, 0.01, 0.05}; methods {A0, A1, A2,
A3, A4, A5}; epsilon = 1e-2; budget 240 oracle calls; = 16 x 2 x 3 x 6 =
**576 cells**, Slurm array `0-575%24`, requeue-safe per-cell checkpoints,
mail END/FAIL/REQUEUE, audit gates `cells=576`. Estimated cost: comparable
to one damping-frontier run (the oracle dominates; stabilized methods should
*reduce* total oracle calls).

## 9. Reproduction

```bash
cd src
python3 experiments/analyze_closeout.py \
    --phase1  ../result/phase1/20260816T180507Z \
    --damping ../result/damping_frontier/20260816T180507Z \
    --boundary ../result/boundary_fine/20260816T180507Z \
    --out ../result/analysis/<new-stamp>
python3 -m pytest tests/test_analysis.py -q
```

The script is deterministic (byte-identical CSVs on identical inputs) and
aborts on any records/checkpoint/SUMMARY disagreement.
