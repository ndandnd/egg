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

**Revision note (2026-08-20 adversarial design review).** This draft was
amended in place: the constructive witness is now fully specified (frozen
depot-return policy P1, dwell construction, charging integration, slot
alignment, terminal-SOC check, tie-breaks); the directional bisection was
replaced by a finite outcome-blind candidate enumeration (Section 4.3
records why the old rule was directionally invalid); the baseline `S0`
must itself pass relevance R1-R2; the confirmation seed band 32-37 is
backed by an in-repository provenance proof; the decision rules use a
direction-SIGNED median with an explicit wrong-direction NO-GO case; the
gate thresholds are explicitly engineering gates, not significance
levels; and Appendix A adds pseudo-code plus a state-transition table
making the screen byte-for-byte reproducible.

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
  *Necessity justification (generator-specific):* charging exists only at
  the depot, so the depot-departure-to-depot-arrival segment containing
  trip `i` consumes at least `dh_kwh(depot, start_i) + energy_i +
  dh_kwh(end_i, depot)` whenever it contains only trip `i`; if the
  segment chains further trips, it consumes strictly more, because the
  generator's minimum trip energy (14.0 kWh) exceeds the largest possible
  deadhead-detour saving (all deadhead energies are <= 2.4 kWh). N2 is
  therefore necessary for THIS generator's frozen `trip_energy_range` and
  deadhead table; it is asserted, not assumed, in the screen record.
- **N3 (terminal SOC):** `soc_min_kwh <= soc_end_kwh <= battery_kwh`.
- **N4 (charge-rate admissibility):** one slot of charging delivers
  `charge_power_kw × slot_min / 60 > 0` kWh (non-degenerate charging).

These are necessary for any feasible schedule; they use only instance data, no
assignment.

### 4.2 Deterministic constructive-duty witness `W` (sufficiency + relevance)

`W` is a fixed, deterministic, no-solver constructor. It establishes
**sufficiency of feasibility** (a witness feasible schedule exists) and
quantifies **relevance** (price-responsive charging exists in that witness).
Every rule below is frozen; Appendix A gives the exact pseudo-code and the
state-transition table so that two independent implementations must select
the same levels byte-for-byte.

**Depot-return policy P1 (frozen).** Vehicles NEVER wait at a trip
endpoint: after serving trip `i` (ending at `end_min_i` at `end_loc_i`)
the vehicle immediately deadheads to the depot, arriving at
`free_at = end_min_i + dh_min(end_loc_i, depot)`. All idle time, and
therefore all charging, occurs at the depot. (Rationale: charging exists
only at the depot in this model; waiting at an endpoint can only forgo
charging options. P1 also makes the earlier "already at start_loc"
tie-break vacuous — between trips every vehicle is at the depot — so
that tie-break is removed.)

**Vehicle state.** `(soc_arr, free_at)` — SOC on depot arrival and the
arrival minute. A new vehicle is available at the depot from minute 0
with `soc_arr = soc0 = battery_kwh`.

**Dwell construction and charging integration (frozen).** For a
candidate assignment of trip `i` to a vehicle, the depot departure
minute is `depart = start_min_i - dh_min(depot, start_loc_i)`; the
dwell is `[free_at, depart]` and requires `depart >= free_at`. Charging
is continuous-time at full power within the dwell, charge-to-full
capped by dwell length:

```
soc_dep = min(battery_kwh,
              soc_arr + charge_power_kw * (depart - free_at) / 60)
```

(IEEE-754 float64, exactly this expression and operand order.)

**Eligibility (frozen).** The vehicle is eligible for trip `i` iff
`depart >= free_at` and the full P1 round segment respects the SOC
floor:

```
soc_dep - (dh_kwh(depot, start_loc_i) + energy_i
           + dh_kwh(end_loc_i, depot)) >= soc_min_kwh
```

(the minimum of the SOC path over the segment is at its end, so this
single inequality is the "soc_min throughout" check under P1).

**Assignment loop (frozen).**

1. Sort trips ascending by `(start_min, id)`.
2. For each trip in order, evaluate eligibility over open vehicles in
   index order; select the eligible vehicle with (i) earliest `free_at`,
   (ii) tie-break lowest vehicle index.
3. If no open vehicle is eligible, open a new vehicle (next index) if
   under `max_vehicles` and assign if eligible (a new full vehicle is
   eligible exactly when bound N2 holds for trip `i`); otherwise `W`
   **fails** (`W-INFEASIBLE`).
4. On assignment, update
   `soc_arr' = soc_dep - dh_kwh(depot,start_i) - energy_i -
   dh_kwh(end_i,depot)` and `free_at' = end_min_i +
   dh_min(end_loc_i, depot)`; record the dwell's charging event with
   `charge_kwh = soc_dep - soc_arr` if strictly positive.

**Terminal-SOC check (frozen).** After all trips are assigned, every
used vehicle is at the depot (P1). Its terminal dwell is
`[free_at, horizon_min]` with `horizon_min = n_slots * slot_min`
(= 1680); terminal charging uses the same integration rule; `W`
requires `min(battery_kwh, soc_arr + charge_power_kw *
(horizon_min - free_at) / 60) >= soc_end_kwh` for every vehicle, and
records the terminal charging event (energy up to the cap) if strictly
positive. A terminal-check failure is `W-INFEASIBLE`.

`W` **witnesses feasibility** iff it assigns all trips within
`max_vehicles` with every dwell/segment inequality and every terminal
check satisfied.

**Relevance from `W` (deterministic; slot alignment frozen).** For a
charging event on dwell `[a, d]` with energy `c > 0`:

- whole slots fully inside the dwell:
  `k = floor(d / slot_min) - ceil(a / slot_min)` (an integer, possibly
  <= 0);
- slots needed:
  `n_c = ceil(c / (charge_power_kw * slot_min / 60))`;
- the event is **timing-free** iff `n_c >= 1` and `k >= n_c + 1`
  (equivalently: at least two distinct contiguous placements of `n_c`
  slots fit in the dwell; for `k >= n_c + 1` the count of contiguous
  placements `k - n_c + 1 >= 2`, and any non-contiguous placement rule
  gives at least as many).

The setting is relevant iff

- **R1 (charging occurs):** total charging energy across all of `W`'s
  events (dwell and terminal) is strictly positive; and
- **R2 (timing has freedom):** at least one charging event is
  timing-free.

### 4.3 Frozen candidate enumeration and outcome-blind selection

**Why not directional bisection.** The earlier draft moved a level "away
from baseline" on a relevance failure. That rule is not directionally
valid for every factor: increasing battery capacity can further REDUCE
charging (R1 gets worse away from baseline on the battery-high side),
and increasing charging power can REDUCE the number of feasible timing
placements a fixed dwell admits (the needed slot count drops, changing
which dwells are timing-free in either direction). Feasibility and
relevance are therefore NOT assumed monotone in any level; the screen
uses a finite deterministic enumeration instead of bisection.

All frozen now (a `b`-independent, outcome-free procedure):

- **Baseline gate first.** The six baseline `S0` instances
  (seeds x n at 60.0 kWh / 150.0 kW) must pass N1-N4, `W` feasibility,
  AND relevance R1-R2. `S0` is fixed and never adjusted; if any baseline
  instance fails any gate, the pilot is `DESIGN-NOT-FROZEN` (Section 6).
  Rationale: every factor effect is measured against `S0`, so the
  baseline must itself exhibit the price-responsive charging margin the
  factors are hypothesized to modulate; otherwise a contrast would
  measure activation of charging rather than modulation of it, which is
  a different estimand.
- **Candidate grids (finite, inclusive, frozen):**
  - `battery_low`: `40.0, 41.0, ..., 55.0` kWh (step 1.0; 16 candidates);
  - `battery_high`: `75.0, 76.0, ..., 120.0` kWh (step 1.0; 46);
  - `power_low`: `50.0, 55.0, ..., 120.0` kW (step 5.0; 15);
  - `power_high`: `200.0, 205.0, ..., 400.0` kW (step 5.0; 41).
- **Outcome-blind lexicographic preference (frozen).** For each level,
  order its candidates by
  1. smaller `|candidate - starting_candidate|` (Section 2.1 starting
     candidates 45/90 kWh, 75/300 kW);
  2. tie-break: larger `|candidate - baseline|`;
  3. (no further tie is possible: two distinct values equidistant from
     the start differ in distance from the baseline).
- **Level acceptance.** A candidate level PASSES iff all six
  `(seed, n)` instances at that level's setting pass N1-N4, `W`
  feasibility, and R1-R2 (instances evaluated in `(seed asc, n asc)`
  order; evaluation is a pure function of the instance and level). The
  **selected level** is the FIRST passing candidate in the preference
  order. Levels are selected independently per setting (S1, S2, S3, S4,
  in that order, for the record; selections do not interact).
- **Non-exercisable classification.** If NO candidate in a level's grid
  passes, that level is **non-exercisable on this grid**; the pilot is
  `DESIGN-NOT-FROZEN` (Section 6) and is revised as a documentation
  event, never run. No step caps or rounding-direction rules exist:
  the enumeration is exhaustive over the frozen finite grid.
- On pass, the four numeric levels are **frozen** (one-way) into the
  Section 7 manifest.

Because the entire screen reads instance structure only — never any
solver outcome — level selection introduces no look-ahead bias, and
because every rule above is a total order over a finite set, two
independent implementations must select identical levels.

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

**Deterministic contrast selection.** Let `s_f` be the setting's
direction sign (`+1` for `S1`, `S3`; `-1` for `S2`, `S4`). For each
setting `f`, let `count_f` be the number of the 12 matched market cells
that are direction-consistent zero-excluding, and

```
med_f = median over the 12 cells of  s_f * midpoint(Delta_f,j)   (SEK)
```

(the DIRECTION-SIGNED median midpoint: positive when the median effect
points in `f`'s preregistered direction). Consider settings in the fixed
order `(S1_batt_low, S2_batt_high, S3_pow_low, S4_pow_high)` and select
the single **selected contrast** `f*` maximizing `count_f`; tie-break by
larger `med_f`; final tie-break by that fixed order. `f*` is defined for
every outcome and is what confirmation (Section 8) will test.

**Resolution threshold (exact, unit-bearing).**

```
tau_Delta = 2 (tol_d + epsilon) = 2 (0.01 + 0.01) = 0.04 SEK,
```

the worst-case matched-contrast width. An effect whose selected-contrast median
midpoint magnitude does not exceed `tau_Delta` cannot be resolved from the
certified intervals.

**States** (evaluated top to bottom; the first that matches is the outcome;
they are mutually exclusive by this ordering):

1. **DESIGN-NOT-FROZEN.** The Section 4 screen did not pass: the
   baseline `S0` fails any of N1-N4 / `W` / R1-R2, or a level's finite
   candidate grid contains no passing candidate (the factor is
   non-exercisable on this grid), or the Section 7 manifest is
   incomplete. The pilot cannot run. (Not evidence.)
2. **INVALID / HALT.** The run executed but is an engineering/validity failure:
   any A2 cell fails to certify within budget, any dictator fails to converge
   (`adaptive_gap > tol_d`), any replay-invalid record, any Section 3
   count/hash/provenance mismatch, or any interval sanity violation
   (`U_hi < U_lo_raw`, `width(U) > tol_d + epsilon`, etc.). This is an
   engineering halt to be repaired and re-run — **it is not scientific
   evidence**, and no cell is ever silently dropped.
3. **UNDER-RESOLVED.** Valid population, but `|med_{f*}| <= tau_Delta`
   (0.04 SEK): the magnitude of the selected contrast's signed median
   midpoint does not exceed the worst-case interval-difference width.
   The pilot is underpowered relative to the certified interval width;
   tighten `epsilon`/`tol_d` before any confirmation. This is **not**
   evidence of absence of an effect.
4. **GO.** Valid population, `med_{f*} > tau_Delta` (resolved AND in the
   preregistered direction), **and** `count_{f*} >= 9` of 12
   (direction-consistent zero-excluding). Proceed to the Section 8
   confirmation on `f*`.
5. **NO-GO.** Valid population and resolved (`|med_{f*}| > tau_Delta`)
   but not a GO: either `count_{f*} < 9`, or the signed median points
   AGAINST the preregistered direction (`med_{f*} < -tau_Delta`). This
   is a **decision not to proceed at this pilot's design and
   resolution**. It is **not** a scientific null: failing the gate does
   not establish that the factor has no effect on the internal uplift.

`GO` and `UNDER-RESOLVED` cannot both fire (`UNDER-RESOLVED` keys on
`|med_{f*}| <= tau_Delta` and is ordered first); `GO` and `NO-GO`
partition the resolved cases exactly.

**Statistical language (frozen).** `9/12` here and `18/24` in Section 8
are **preregistered engineering gates** — deterministic thresholds a
future run must meet to justify the next engineering step. They are NOT
hypothesis-test significance levels, carry no p-value or error-rate
calibration, and no inferential claim may be attached to meeting or
missing them.

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
- **Seed-band provenance (verified in-repository, 2026-08-20):** every
  committed driver of this generator/evidence family pins its seeds
  below 32 — `run_phase1.py` (default seeds 0–3, campaign grids ⊆ 0–15),
  `run_b2_expansion.py` (`ALL_SEEDS = tuple(range(16))`),
  `run_phase2.py`/boundary (seeds 0–7), `run_a6_pilot.py` and
  `local_a6_preflight.py` (burned `{0, 11, 15}`), and
  `run_a6_holdout.py` (`SEEDS = tuple(range(16, 32))`, the reserved
  band). A repository-wide scan (drivers, results, refs, docs) finds no
  reference to any seed ≥ 32 for `synthetic_instance`. The band 32–37 is
  therefore demonstrably untouched; this was established from code and
  manifests only, without reading any outcome.
- **Selected contrast:** exactly the `f*` chosen by the frozen deterministic
  rule of Section 6 (the rule, not its identity, is fixed in advance);
  confirmation tests only `S0` versus `S_{f*}`.
- **Grid & method:** the confirmation cells are
  `6 seeds × n{8,12} × b{0.01,0.05} × {S0, S_{f*}} = 48` A2 cells and 48
  dictators; matched contrasts `= 6 × 2 × 2 = 24`.
- **Denominator:** `24` matched contrasts.
- **Threshold (frozen):** replicate iff the `f*` contrast is direction-consistent
  zero-excluding on `>= 18/24` (the same 75% engineering gate as `9/12`;
  not a significance level) **and** the confirmation direction-signed
  median midpoint `med` (the Section 6 convention, computed over the 24
  matched contrasts) exceeds `tau_Delta = 0.04 SEK`.
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

---

## Appendix A. Screen pseudo-code and state-transition table (normative)

Two independent implementations following this appendix must select the
same levels byte-for-byte. All arithmetic is IEEE-754 float64 with the
exact expressions and operand orders shown; all candidate values are
exact decimal grid points; no randomness, no wall clock, no solver.

### A.1 Witness pseudo-code (policy P1)

```
def witness(inst):                      # inst: one physical instance
    trips = sort(inst.trips, key=(start_min, id))
    vehicles = []                       # list of (soc_arr, free_at)
    events = []                        # charging events (a, d, kwh)
    for trip in trips:
        depart = trip.start_min - inst.dh_min[(inst.depot, trip.start_loc)]
        need = (inst.dh_kwh[(inst.depot, trip.start_loc)]
                + trip.energy_kwh
                + inst.dh_kwh[(trip.end_loc, inst.depot)])
        chosen = None
        for v_index in 0 .. len(vehicles)-1:          # index order
            (soc_arr, free_at) = vehicles[v_index]
            if depart < free_at: continue
            soc_dep = min(inst.battery_kwh,
                          soc_arr + inst.charge_power_kw
                                    * (depart - free_at) / 60)
            if soc_dep - need < inst.soc_min_kwh: continue
            if chosen is None or free_at < chosen.free_at \
               or (free_at == chosen.free_at and v_index < chosen.index):
                chosen = (v_index, soc_dep, free_at)
        if chosen is None:
            if len(vehicles) == inst.max_vehicles: return W_INFEASIBLE
            v_index = len(vehicles)                  # new depot vehicle
            soc_arr, free_at = inst.battery_kwh, 0
            depart_ok = depart >= 0
            soc_dep = min(inst.battery_kwh,
                          soc_arr + inst.charge_power_kw
                                    * (depart - free_at) / 60)
            if not depart_ok or soc_dep - need < inst.soc_min_kwh:
                return W_INFEASIBLE                  # == N2 failure
            vehicles.append((soc_arr, free_at))
            chosen = (v_index, soc_dep, free_at)
        (v_index, soc_dep, free_at) = chosen
        if soc_dep - vehicles[v_index].soc_arr > 0:
            events.append((free_at, depart,
                           soc_dep - vehicles[v_index].soc_arr))
        vehicles[v_index] = (
            soc_dep - need,
            trip.end_min + inst.dh_min[(trip.end_loc, inst.depot)])
    horizon = inst.n_slots * inst.slot_min
    for (soc_arr, free_at) in vehicles:              # terminal checks
        soc_final = min(inst.battery_kwh,
                        soc_arr + inst.charge_power_kw
                                  * (horizon - free_at) / 60)
        if soc_final < inst.soc_end_kwh: return W_INFEASIBLE
        if soc_final - soc_arr > 0:
            events.append((free_at, horizon, soc_final - soc_arr))
    return W_FEASIBLE, events
```

### A.2 Relevance pseudo-code

```
def relevant(inst, events):
    if sum(kwh for (_, _, kwh) in events) <= 0: return R1_FAIL
    per_slot = inst.charge_power_kw * inst.slot_min / 60
    for (a, d, kwh) in events:
        k = floor(d / inst.slot_min) - ceil(a / inst.slot_min)
        n_c = ceil(kwh / per_slot)
        if n_c >= 1 and k >= n_c + 1: return RELEVANT
    return R2_FAIL
```

### A.3 Screen driver pseudo-code

```
def screen():
    # baseline gate (S0 fixed at 60.0 kWh / 150.0 kW)
    for (seed, n) in (0,8),(0,12),(11,8),(11,12),(15,8),(15,12):
        inst = synthetic_instance(seed, n)           # frozen defaults
        if not (N1..N4(inst) and witness(inst) is W_FEASIBLE
                and relevant(...) is RELEVANT):
            return DESIGN_NOT_FROZEN("baseline")
    frozen = {}
    for level in (S1_batt_low, S2_batt_high, S3_pow_low, S4_pow_high):
        for cand in preference_order(level):         # Section 4.3
            if all((N1..N4 and W_FEASIBLE and RELEVANT)
                   for the six (seed, n) instances at cand):
                frozen[level] = cand; break
        else:
            return DESIGN_NOT_FROZEN(level)          # non-exercisable
    return FROZEN(frozen)                            # -> Section 7 manifest
```

### A.4 State-transition table (per level; per candidate)

| state | condition | next state |
| --- | --- | --- |
| `CANDIDATE(c)` | any of N1-N4 fails on any of the 6 instances | `REJECT(c, infeasible-bound)` -> next candidate |
| `CANDIDATE(c)` | bounds pass; `witness` returns `W_INFEASIBLE` on any instance | `REJECT(c, witness-infeasible)` -> next candidate |
| `CANDIDATE(c)` | witness feasible everywhere; `R1_FAIL` on any instance | `REJECT(c, no-charging)` -> next candidate |
| `CANDIDATE(c)` | R1 passes everywhere; `R2_FAIL` on any instance | `REJECT(c, no-timing-freedom)` -> next candidate |
| `CANDIDATE(c)` | all gates pass on all 6 instances | `SELECTED(c)` — level frozen |
| (candidates exhausted) | no `SELECTED` | `NON-EXERCISABLE` -> `DESIGN-NOT-FROZEN` |

Baseline `S0` runs the same per-instance gates once, with no candidate
loop: any failure is directly `DESIGN-NOT-FROZEN`.

Every `REJECT`/`SELECTED` transition, with its candidate value, gate,
first failing `(seed, n)` instance, and gate-specific measurements, is
part of the emitted screen record (Section 7) and must regenerate
byte-identically.
