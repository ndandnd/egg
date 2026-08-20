# B3 internal-uplift factor pilot — preregistration DRAFT

Status: **DRAFT — not authorized to run.** This specification is a proposal
only. It is explicitly dependent on the independent review of the retrospective
no-solver B3 baseline in
[PR #30](https://github.com/ndandnd/egg/pull/30) ("B3 no-solver
certified-uplift baseline (four-way audited, paired effects, retrospective)").
No cluster experiment, local solve, or compute of any kind is authorized by
this document. It adds no code, driver, launcher, or configuration; it changes
no existing file. The frozen algorithm/grid files, experiment drivers, the
launcher, the runbook, the decision/status logs, PR #28/#30 files, and
everything under `src/runs/` are untouched.

This pilot studies **B3: the internal-uplift atlas** — how the certified price
of indivisibility responds to two physical fleet parameters — using only **A2
(certified convex-hull column generation) plus independent dictator evidence**.
No A6 method, no A6 code path, and no A6 outcome is used, read, or referenced.

Cross-references (background only; not modified by this draft):
`ref/BRAINSTORM_20260814.md` (B1–B3 internal-uplift atlas),
`ref/RESEARCH_DIRECTIONS.md` Section 4 (execution priorities),
`doc/MEASUREMENT_RESULTS.md` Section 8 (the existing 12-cell B2-A2 pilot),
`doc/B2_STABILIZATION_SPEC.md`, PR #30's `doc/B3_UPLIFT_BASELINE_SPEC.md`
(the retrospective baseline this pilot extends), and the queued-work note
carried into the E1–E4 closeout handoff (the no-solver B3 baseline and *its
factor-pilot specification* must both be reviewed before any new cluster
experiment starts).

---

## 1. Object of study and the certified uplift interval

For a fixed instance and market, let

- `z_CH` = the convex-hull (LP-relaxation-over-columns) system optimum that A2
  certifies to absolute tolerance `epsilon`, bracketed by the running upper
  bound `ub_CH` and the certified lower bound `lb_CH` (`lb_best`), with
  `ub_CH >= z_CH >= lb_CH` and `ub_CH - lb_CH <= epsilon`;
- `z_D` = the dictator (integer, physically feasible) system optimum, solved
  independently and adaptively certified to absolute tolerance `tol_d`, with a
  feasible upper value `z_D_ub` and a certified lower bound `z_D_lb`
  (`z_D_ub >= z_D >= z_D_lb` and `z_D_ub - z_D_lb <= tol_d`).

The **internal uplift** (B3) is the price of indivisibility
`U = z_D - z_CH >= 0` (the theorem `z_D >= z_CH`), i.e. the MIP–LP /
dictator-vs-convex-hull gap of the integrated economy.

### 1.1 Certified interval (corrected)

The existing B2-A2 pilot emits, per cell (see `run_b2a2_pilot.py` and
`b2a2.finish`),

```
U_lo_raw = (z_D_ub - tol_d) - ub_CH          # dictator LB proxy
U_hi     = z_D_ub - lb_CH
U = [U_lo_raw, U_hi].
```

**Interval width.** By construction

```
width(U) = U_hi - U_lo_raw = tol_d + (ub_CH - lb_CH)  <=  tol_d + epsilon.
```

The convex-hull PWL/outer-approximation slack is **already contained** in
`ub_CH - lb_CH`; it is not an additional term. (This corrects the earlier
"`epsilon + tol_d` plus PWL slack" phrasing.)

**Lower-bound handling.**
- The raw endpoint `U_lo_raw` is always retained and disclosed.
- The theorem `z_D >= z_CH` tightens the reported lower bound to
  `U_lo = max(0, U_lo_raw)`; both `U_lo_raw` and `max(0, U_lo_raw)` are
  reported (identical convention to PR #30's baseline).
- **Prefer the actual dictator lower bound when recorded.** The dictator stage
  records a certified lower bound `z_D_lb` (the adaptive lower bound in
  `sol.stats.extra["adaptive_lb"]`, with `z_D_lb >= z_D_ub - tol_d`). When
  `z_D_lb` is present in the evidence, use `U_lo_raw = z_D_lb - ub_CH` (a
  tighter, exact endpoint) in place of the `(z_D_ub - tol_d)` proxy; the proxy
  is a documented fallback only.

**Normalization.** Following PR #30, the primary normalization is **per-trip**
(`U / n_trips`, a division by a positive integer constant, so the interval
scales rigorously). A cost-fraction `U / z_CH` is reported **only when
`lb_CH > 0`**, as the rigorous interval quotient
`[max(0, U_lo_raw)/ub_CH, U_hi/lb_CH]` (smallest denominator for the upper
endpoint, largest for the lower); when `lb_CH <= 0` it is omitted, never
approximated.

This pilot treats the interval as the primary certified observable and never
collapses it to a point.

## 2. Design: two physical factors, five one-at-a-time settings

Two generator parameters are varied (both first-class `Instance` fields and
`synthetic_instance` arguments; no code change is implied):

| Factor | Generator knob | Units | Baseline |
| --- | --- | --- | --- |
| Battery capacity | `battery_kwh` (**changes the entire SOC envelope**: `soc0`, `soc_min`, `soc_end` all scale at the fixed 0.10/0.10 fracs) | kWh | 60.0 |
| Per-vehicle charging power | `charge_power_kw` | kW | 150.0 |

The design is **one-factor-at-a-time (OFAT) about a common baseline**, giving
five *physical settings*:

| Setting | direction sign (H1/H2) | `battery_kwh` | `charge_power_kw` | Meaning |
| --- | --- | --- | --- | --- |
| `S0_baseline` | — | baseline | baseline | shared reference |
| `S1_batt_low` | Δ ≥ 0 (non-negative) | low | baseline | tighter battery |
| `S2_batt_high` | Δ ≤ 0 (non-positive) | high | baseline | looser battery |
| `S3_pow_low` | Δ ≥ 0 (non-negative) | baseline | low | slower charging |
| `S4_pow_high` | Δ ≤ 0 (non-positive) | baseline | high | faster charging |

### 2.1 Candidate levels (NOT yet frozen)

Provisional inputs to the deterministic screen of Section 4; frozen **only
after** the screen passes, and never against any outcome.

| Factor | low candidate | baseline | high candidate |
| --- | --- | --- | --- |
| `battery_kwh` | 45.0 | 60.0 | 90.0 |
| `charge_power_kw` | 75.0 | 150.0 | 300.0 |

All other generator arguments (trip-energy range, day window, deadhead links,
slots, `soc_*_frac`, `vehicle_fixed_cost`, `dh_cost_per_min`, `max_vehicles`)
are held at their current defaults and are part of the frozen provenance.

## 3. Population and exact counts (corrected terminology)

Burned **development** seeds and grid:

- seeds `{0, 11, 15}` (development only),
- `n_trips ∈ {8, 12}`,
- `b ∈ {0.01, 0.05}` (affine market depth, `shape="duck"`),
- method **A2 only**, `epsilon = 1e-2`, `budget = 240`, `tol_d = 1e-2`.

Because `b` is a **market** parameter, it does not enter the `Instance` object.
The population must therefore be described at two levels:

```
unique physical setting-instances = seeds × n × settings = 3 × 2 × 5 = 30
instance-market cells             = × b (2)               = 60
unique baseline physical instances = seeds × n × {S0}     = 3 × 2 = 6
baseline market cells             = × b (2)               = 12
A2 method-cells                   = 60   (exactly)
independent dictator solves       = 60   (one per cell; z_D depends on b)
matched factor-minus-baseline contrasts = per (seed,n,b) × 4 = 12 × 4 = 48
strata                            = (n × b) = 4, crossed with 3 seeds
```

**Hash relationships (asserted in provenance):** `Instance.hash()` is
**identical across the two `b` values** for a fixed `(seed, n, setting)` (30
distinct instance hashes appearing twice each = 60 cell rows); **market hashes
differ across `b`** (and, via `n_slots`/duck shape, are cell-specific). The 6
baseline physical instances each appear in 2 market cells (12 baseline cells).

The generator-only screen of Section 4 runs on the **30 unique physical
setting-instances** (it is `b`-independent, being structural). Hard exclusions
(preregistered): **no seeds 16–31** (a reserved band, untouched), and **no A6
method or A6 code path** anywhere.

## 4. Generator-only feasibility / relevance screen (schedule-independent)

The screen must not depend on any optimizer's endogenous duties, depot visits,
dwell windows, or per-vehicle energies. It is defined as **schedule-independent
necessary bounds** plus a **deterministic constructive-duty witness** — no
solver, fully specified, deterministic.

### 4.1 Schedule-independent necessary bounds (fast reject)

Computed from instance fields only (`trips`, `dh_kwh`, `battery_kwh`,
`soc_min_kwh`, `soc_end_kwh`, `charge_power_kw`, `slot_min`); a failure of any
bound rejects the setting before the witness runs. Let usable band
`B = battery_kwh - soc_min_kwh`.

- **N1 (per-trip energy):** for every trip `i`, `energy_i <= B`.
- **N2 (depot round-trip):** for every trip `i`,
  `dh_kwh(depot, start_i) + energy_i + dh_kwh(end_i, depot) <= B`
  (a fully charged vehicle can pull out, serve `i`, and pull in).
- **N3 (terminal SOC):** `soc_min_kwh <= soc_end_kwh <= battery_kwh`.
- **N4 (charge-rate admissibility):** one slot of charging delivers
  `charge_power_kw × slot_min / 60 > 0` kWh (non-degenerate charging).

These are necessary for any feasible schedule; they use only instance data, no
assignment.

### 4.2 Deterministic constructive-duty witness `W` (sufficiency + relevance)

`W` is a fixed, deterministic, no-solver constructor. It establishes
**sufficiency of feasibility** (a witness feasible schedule exists) and
quantifies **relevance** (price-responsive charging exists in that witness).

Construction (all rules fixed; no optimization):

1. Sort trips ascending by `(start_min, id)`.
2. Maintain vehicle states `(location, soc, free_at)`; at most `max_vehicles`.
   Every vehicle begins the day at the depot with `soc = soc0 = battery`.
3. For each trip in order, the **eligible** vehicles are those that can deadhead
   from their current location to `start_loc` by `start_min`, serve the trip,
   and retain the ability to pull in to the depot, all with `soc >= soc_min`
   throughout (charging to full is applied whenever the vehicle is idle at the
   depot; see rule 5). Select the eligible vehicle by fixed tie-break:
   (i) already at `start_loc`; else (ii) earliest `free_at`; else (iii) lowest
   vehicle index. If none is eligible, open a new depot vehicle if under
   `max_vehicles`; otherwise `W` **fails**.
4. SOC is integrated exactly along each constructed duty using `dh_kwh` and trip
   `energy`.
5. **Charging rule (fixed):** a vehicle charges only at the depot, only during
   idle dwell, at `charge_power_kw`, charging to full on each depot visit before
   its next departure; charged energy per dwell is capped by dwell length on the
   `slot_min` grid.

`W` **witnesses feasibility** iff it assigns all trips within `max_vehicles`
with every duty satisfying `soc_min` throughout and `soc_end` at pull-in.

**Relevance from `W` (deterministic):** the setting is relevant iff
- **R1 (charging occurs):** total depot charging energy across `W`'s duties is
  strictly positive (a full-battery day would otherwise need no charge — uplift
  would be price-insensitive); and
- **R2 (timing has freedom):** at least one charging event in `W` admits ≥ 2
  distinct feasible `slot_min` placements within its depot dwell (so *when* to
  charge, and thus the price paid, is a live decision).

### 4.3 Frozen search bands, rounding, stopping, directions, steps, tie-breaks

All frozen now (a `b`-independent, outcome-free procedure over the 30 unique
physical instances):

- **Search bands (inclusive):** `battery_low ∈ [40.0, 55.0]` kWh,
  `battery_high ∈ [75.0, 120.0]` kWh, `power_low ∈ [50.0, 120.0]` kW,
  `power_high ∈ [200.0, 400.0]` kW. Baseline `60.0` kWh / `150.0` kW is fixed
  and never adjusted.
- **Rounding grid:** battery to the nearest `1.0` kWh; power to the nearest
  `5.0` kW. Half-way values round toward baseline for feasibility adjustments
  and toward the band edge for relevance adjustments.
- **Starting candidates:** Section 2.1 (`45/90` kWh, `75/300` kW).
- **Adjustment directions:** a **feasibility** failure (N1–N4 or `W` fails)
  moves the offending level **toward baseline** by bisection of the
  level-to-baseline distance; a **relevance** failure (R1/R2) moves it **away
  from baseline** by bisection of the level-to-band-edge distance. Then re-round
  and re-screen.
- **Evaluation order (deterministic):** instances in `(seed asc, n asc,
  setting order S0…S4)`; the first failing `(instance, level)` in that order
  drives the single adjustment for that level.
- **Stopping rule:** the screen passes when all 30 unique physical instances
  satisfy N1–N4 and (for the four non-baseline settings) `W` feasibility with
  R1–R2. On pass, the four numeric levels are **frozen** (one-way) into the
  Section 7 manifest.
- **Maximum steps:** at most **4** bisection steps per level (≤ 8 per factor).
  If a level cannot pass within the step cap or would leave its band, that
  factor is **not exercisable** on this grid → state `DESIGN-NOT-FROZEN`
  (Section 6); the pilot is revised as a documentation event, never run.

Because the entire screen reads no outcome, level adjustment introduces no
look-ahead bias.

## 5. Measurement

For each of the 60 cells (in a future, reviewed run): solve the dictator
independently (adaptive, `tol_d`), then run A2 certified CG with the dictator
evidence feeding the interval of Section 1.1. Record, per cell, the certified
`U = [U_lo_raw, U_hi]`, the theorem-tightened `max(0, U_lo_raw)`, the preferred
`z_D_lb`-based endpoint when recorded, the per-trip normalization, and (only if
`lb_CH > 0`) the rigorous cost-fraction interval.

**Matched factor-minus-baseline interval effects.** For each `(seed, n, b)` and
setting `f ∈ {S1,S2,S3,S4}`, the effect versus the same market cell's baseline
`S0` is the rigorous interval difference

```
Delta_f = U_f - U_0 = [ U_f_lo_raw - U_0_hi ,  U_f_hi - U_0_lo_raw ],
width(Delta_f) = width(U_f) + width(U_0) <= 2 (tol_d + epsilon) = 0.04 SEK.
```

Matching is on the market-cell identity `(seed, n, b)`; the two cells differ
only in the one screened physical factor. `midpoint(Delta_f)` and its magnitude
`|midpoint|` are used only by the deterministic decision rules of Section 6; no
effect is reported as a point.

## 6. Preregistered decision taxonomy (ordered, mutually exclusive)

Hypotheses (directional, fixed before any outcome), with the per-setting signs
of the Section 2 table:

- **H1 (battery):** tightening (`S1`) does not decrease uplift (`Δ ≥ 0`);
  loosening (`S2`) does not increase it (`Δ ≤ 0`).
- **H2 (power):** slower charging (`S3`) does not decrease uplift (`Δ ≥ 0`);
  faster charging (`S4`) does not increase it (`Δ ≤ 0`).

**Direction-consistent zero-exclusion.** A matched contrast `Delta_f,j` is
*direction-consistent zero-excluding* iff it strictly excludes 0 in `f`'s
preregistered direction: `Delta_f,j_lo > 0` for a non-negative-direction setting
(`S1`, `S3`), or `Delta_f,j_hi < 0` for a non-positive-direction setting (`S2`,
`S4`).

**Deterministic contrast selection.** For each setting `f`, let `count_f` be the
number of the 12 matched instances that are direction-consistent zero-excluding,
and `med_f` the median over the 12 of the direction-signed `|midpoint(Delta_f)|`
(SEK). Consider settings in the fixed order
`(S1_batt_low, S2_batt_high, S3_pow_low, S4_pow_high)` and select the single
**selected contrast** `f*` maximizing `count_f`; tie-break by larger `med_f`;
final tie-break by that fixed order. `f*` is defined for every outcome and is
what confirmation (Section 8) will test.

**Resolution threshold (exact, unit-bearing).**

```
tau_Delta = 2 (tol_d + epsilon) = 2 (0.01 + 0.01) = 0.04 SEK,
```

the worst-case matched-contrast width. An effect whose selected-contrast median
midpoint magnitude does not exceed `tau_Delta` cannot be resolved from the
certified intervals.

**States** (evaluated top to bottom; the first that matches is the outcome;
they are mutually exclusive by this ordering):

1. **DESIGN-NOT-FROZEN.** The Section 4 screen did not pass, a level hit the
   step cap or left its band, a factor is not exercisable, or the Section 7
   manifest is incomplete. The pilot cannot run. (Not evidence.)
2. **INVALID / HALT.** The run executed but is an engineering/validity failure:
   any A2 cell fails to certify within budget, any dictator fails to converge
   (`adaptive_gap > tol_d`), any replay-invalid record, any Section 3
   count/hash/provenance mismatch, or any interval sanity violation
   (`U_hi < U_lo_raw`, `width(U) > tol_d + epsilon`, etc.). This is an
   engineering halt to be repaired and re-run — **it is not scientific
   evidence**, and no cell is ever silently dropped.
3. **UNDER-RESOLVED.** Valid population, but the selected contrast's `med_{f*}
   <= tau_Delta` (0.04 SEK). The pilot is underpowered relative to the certified
   interval width; tighten `epsilon`/`tol_d` before any confirmation. This is
   **not** evidence of absence of an effect.
4. **GO.** Valid population, `med_{f*} > tau_Delta`, **and**
   `count_{f*} >= 9` of 12 (direction-consistent zero-excluding). Proceed to
   the Section 8 confirmation on `f*`.
5. **NO-GO.** Valid population, `med_{f*} > tau_Delta`, but `count_{f*} < 9`.
   This is a **decision not to proceed at this pilot's design and resolution**.
   It is **not** a scientific null: failing to reach 9/12 does not establish
   that the factor has no effect on the internal uplift.

`GO` and `UNDER-RESOLVED` cannot both fire (both key on `med_{f*}` versus
`tau_Delta`, and `UNDER-RESOLVED` is ordered first); `GO` and `NO-GO` are
mutually exclusive by the `count_{f*}` test on the same selected contrast.

## 7. Provenance and reproducibility requirements

Any future run implementing this spec must, before scoring:

- Freeze and record, in a manifest with a SHA-256 over its exact bytes: the
  five settings' numeric `battery_kwh`/`charge_power_kw`, all held-fixed
  generator arguments, the seed/`n`/`b` grid, `epsilon`, `budget`, `tol_d`,
  `tau_Delta`, the solver identity (backend + MIP gap), and the
  load-reconstruction policy version.
- Record the exact `Instance.hash()` for all **30 unique physical
  setting-instances** and the market hash for all **60 cells**; assert that each
  instance hash appears exactly twice (once per `b`) and that market hashes are
  distinct across `b`; assert the 6 baseline instances are bit-identical to the
  `S0` cells of the same `(seed, n)`.
- Assert the exact counts of Section 3 (30 physical instances, 60 cells, 6/12
  baselines, 60 dictators, 48 matched contrasts).
- Emit the deterministic screen record (frozen levels, per-instance N1–N4 and
  `W`/R1–R2 results) as a pure function of the manifest; regenerate the screen
  and analysis **byte-identically** on re-run.
- Carry, per record, `U_lo_raw`, `max(0, U_lo_raw)`, the `z_D_lb`-based endpoint
  when recorded, `U_hi`, both certificate gaps, and the per-trip normalization;
  never substitute a point estimate.
- Bind the pilot's git commit (full 40-char SHA) and this document's hash into
  the emitted artifacts; refuse a dirty tracked tree; refuse an existing output
  directory; never modify committed inputs or anything under `src/runs/`.

This draft implements none of the above; it specifies them.

## 8. Separate fresh-seed confirmation stage (frozen now)

The development grid `{0, 11, 15}` is for design and calibration only. The
following confirmation parameters are **frozen now, before any development
outcome**:

- **Confirmation seeds (frozen list):** `{32, 33, 34, 35, 36, 37}` — **count 6**
  — disjoint from the development seeds `{0,11,15}` and from the reserved
  `16–31` band.
- **Selected contrast:** exactly the `f*` chosen by the frozen deterministic
  rule of Section 6 (the rule, not its identity, is fixed in advance);
  confirmation tests only `S0` versus `S_{f*}`.
- **Grid & method:** the confirmation cells are
  `6 seeds × n{8,12} × b{0.01,0.05} × {S0, S_{f*}} = 48` A2 cells and 48
  dictators; matched contrasts `= 6 × 2 × 2 = 24`.
- **Denominator:** `24` matched contrasts.
- **Threshold (frozen):** replicate iff the `f*` contrast is direction-consistent
  zero-excluding on `>= 18/24` (the 75% supermajority matching `9/12`) **and**
  the confirmation median `|midpoint|` exceeds `tau_Delta = 0.04 SEK`.
- **Levels are not re-tuned** on confirmation; the Section 4 screen is re-applied
  at the already-frozen levels to the fresh instances.
- **Screen-failure disposition (frozen):** if the generator-only screen fails
  for any confirmation instance at the frozen levels, the confirmation is
  `DESIGN-NOT-FROZEN` for the fresh grid — report and stop; **do not** re-tune
  levels or seeds. Any certification/convergence/replay failure in the
  confirmation run is `INVALID / HALT`, not a replication verdict.
- **One look:** a single confirmation run; no iteration, no level changes, no
  second look.

Only a passed confirmation justifies proposing any larger or cluster-scale B3
factor campaign; that proposal is a later, separate document.

## 9. Interpretation limits of OFAT

The design estimates **only four local, finite, one-factor contrasts** around a
single baseline. It therefore **cannot**:

- infer any **interaction** between battery capacity and charging power (no
  off-baseline combinations are measured);
- establish **global monotonicity** of uplift in either factor (only two finite
  steps per factor are observed);
- support **general causal** claims beyond the specific finite contrasts on the
  frozen synthetic grid.

Additionally, the battery contrast is **not** an isolated capacity change: at
the fixed 0.10/0.10 fracs, changing `battery_kwh` changes the **entire SOC
envelope** (`soc0`, `soc_min`, `soc_end`), so `S1`/`S2` measure a joint SOC-band
change, not capacity in isolation.

## 10. Scientific boundary (from PR #30, adapted)

Stated here and required in every emitted SUMMARY of any future run:

- All instances are **synthetic**.
- Only **battery capacity and per-vehicle charging power** are varied (across the
  five OFAT settings); all other physics are fixed.
- There is **no shared charger-count / depot-capacity** constraint.
- There is **no V2G**.
- The affine duck-shaped price environment is **not a solar-generation model**.
- `n_trips` is **workload / problem size, not controlled fleet size**.
- There is **no distribution network or locational charging**.
- This is a **minimal two-factor physics slice, not the full B3 atlas**.
- Any result establishes **certified synthetic signal and heterogeneity only —
  not external validity or manuscript-grade novelty**.

## 11. Boundaries and non-goals

- **A2 + dictator evidence only.** No A6 method, no A6 code path, no A6 outcome
  is used or inspected.
- **No seeds 16–31** anywhere; the reserved band is untouched.
- **No compute here.** This document launches nothing, invokes no solver, and
  adds/edits no driver, launcher, runbook, decision/status log, PR #28/#30
  file, or anything under `src/runs/`.
- **Draft, pending review.** Every quantity above is a proposal. The pilot may
  not be preregistered or run until this specification and the retrospective
  no-solver B3 baseline in [PR #30](https://github.com/ndandnd/egg/pull/30) are
  independently reviewed; frozen levels additionally require the Section 4
  generator-only screen to pass.

## 12. Open questions for reviewers

1. Are OFAT contrasts sufficient for the atlas, or is a later full battery ×
   power grid required (at a larger, separately proposed cell budget) to reach
   interactions and monotonicity?
2. Are the candidate ranges (Section 2.1) and the frozen search bands / rounding
   (Section 4.3) physically appropriate?
3. Are `count >= 9/12` (development) and `>= 18/24` (confirmation), with
   `tau_Delta = 0.04 SEK`, the right preregistered thresholds given
   `width(U) <= tol_d + epsilon = 0.02 SEK`?
4. Should `epsilon`/`tol_d` be tightened up front to lower `tau_Delta` and avoid
   an `UNDER-RESOLVED` outcome, at additional solve cost?
5. Should the confirmation seed count exceed 6 to raise replication power before
   any cluster-scale proposal?
