# B3 internal-uplift factor pilot — preregistration DRAFT

Status: **DRAFT — not authorized to run.** This specification is a proposal
only. It is explicitly dependent on the independent review of the retrospective
no-solver B3 baseline in
[PR #30](https://github.com/ndandnd/egg/pull/30) ("B3 no-solver
certified-uplift baseline (four-way audited, paired effects, retrospective)").
No cluster experiment, local solve, or compute of any kind is authorized by
this document. It adds no code, driver, launcher, or configuration; it changes
no existing file. The frozen algorithm/grid files, experiment drivers, the
launcher, the runbook, the decision/status logs, and everything under
`src/runs/` are untouched.

This pilot studies **B3: the internal-uplift atlas** — how the certified price
of indivisibility responds to physical fleet parameters — using only **A2
(certified convex-hull column generation) plus independent dictator evidence**.
No A6 method, no A6 code path, and no A6 outcome is used, read, or referenced.

Cross-references (background only; not modified by this draft):
`ref/BRAINSTORM_20260814.md` (B1–B3 internal-uplift atlas),
`ref/RESEARCH_DIRECTIONS.md` Section 4 (execution priorities),
`doc/MEASUREMENT_RESULTS.md` Section 8 (the existing 12-cell B2-A2 pilot),
`doc/B2_STABILIZATION_SPEC.md`, and the queued-work note carried into the
E1–E4 closeout handoff (the no-solver B3 baseline and *its factor-pilot
specification* must both be reviewed before any new cluster experiment starts).

---

## 1. Object of study and the certified uplift interval

For a fixed instance and market, let

- `z_CH` = the convex-hull (LP-relaxation-over-columns) system optimum that A2
  certifies to tolerance `epsilon`, bracketed by the running upper bound
  `ub_CH` and the certified lower bound `lb_best_CH`;
- `z_D`  = the dictator (integer, physically feasible) system optimum, solved
  independently and adaptively certified to tolerance `tol_d`, with feasible
  value `z_D_ub` and certified lower bound.

The **internal uplift** (B3) is the price of indivisibility

```
U = z_D - z_CH   >= 0,
```

i.e. the MIP–LP / dictator-vs-convex-hull gap of the integrated economy. The
existing B2-A2 pilot already emits it per cell as a **certified interval**
(see `run_b2a2_pilot.py` and `b2a2.finish`):

```
uplift_interval = [ (z_D_ub - tol_d) - ub_CH ,  z_D_ub - lb_best_CH ].
```

Write `U = [U_lo, U_hi]` with `U_lo = (z_D_ub - tol_d) - ub_CH` and
`U_hi = z_D_ub - lb_best_CH`. Both endpoints are rigorous given the two
independent certificates; the interval width is bounded by
`epsilon + tol_d` plus the (recorded, visible) PWL slack. This pilot treats
that interval as the primary certified observable and never collapses it to a
point estimate.

## 2. Design: two physical factors, five one-at-a-time settings

Two generator parameters are varied (both already first-class fields of
`Instance` and arguments of `synthetic_instance`; no code change is implied):

| Factor | Generator knob | Units | Baseline |
| --- | --- | --- | --- |
| Battery capacity | `battery_kwh` (drives `soc0`, `soc_min`, `soc_end` at fixed fracs 0.10/0.10) | kWh | 60.0 |
| Per-vehicle charging power | `charge_power_kw` | kW | 150.0 |

The design is **one-factor-at-a-time (OFAT) about a common baseline**, giving
exactly five *physical settings* per base instance:

| Setting | `battery_kwh` | `charge_power_kw` | Meaning |
| --- | --- | --- | --- |
| `S0_baseline` | baseline | baseline | shared reference |
| `S1_batt_low` | low | baseline | tighter battery |
| `S2_batt_high` | high | baseline | looser battery |
| `S3_pow_low` | baseline | low | slower charging |
| `S4_pow_high` | baseline | high | faster charging |

OFAT (not a full 3×3 grid) is deliberate: it yields clean **matched
factor-minus-baseline** contrasts at exactly 60 A2 cells, and it keeps every
non-baseline setting one physical step from a common, screened reference.

### 2.1 Candidate levels (NOT yet frozen)

Candidate numeric levels below are provisional inputs to the generator-only
screen in Section 4. They are **frozen only after** the screen passes; nothing
downstream may read an outcome before the freeze.

| Factor | low candidate | baseline | high candidate |
| --- | --- | --- | --- |
| `battery_kwh` | 45.0 | 60.0 | 90.0 |
| `charge_power_kw` | 75.0 | 150.0 | 300.0 |

All other generator arguments (trip-energy range, day window, deadhead links,
slots, `soc_*_frac`, `vehicle_fixed_cost`, `dh_cost_per_min`) are held at their
current defaults and are part of the frozen provenance.

## 3. Instance grid and exact counts

Burned **development** seeds and grid (identical to the existing B2-A2 pilot):

- seeds `{0, 11, 15}` (development only),
- `n_trips ∈ {8, 12}`,
- `b ∈ {0.01, 0.05}` (affine market depth, `shape="duck"`),
- method **A2 only**, `epsilon = 1e-2`, `budget = 240`, `tol_d = 1e-2`.

Base instances: `3 × 2 × 2 = 12`. Physical settings: `5`.

```
A2 method-cells        = 12 base instances × 5 settings = 60   (exactly)
paired dictator solves = 60   (one independent dictator per A2 cell)
baseline uplift intervals            = 12   (S0 per base instance)
matched factor-minus-baseline effects = 12 × 4 (S1..S4 − S0) = 48
strata                 = (n × b) = 4, crossed with 3 seeds
```

Hard exclusions (preregistered): **no seeds 16–31**, and **no A6 method or A6
code path** anywhere in this pilot. Seeds 16–31 are reserved and are not touched
here; the fresh-seed confirmation stage (Section 8) draws from a preregistered
range disjoint from both the development seeds and any reserved band.

## 4. Generator-only feasibility / relevance screen (before freezing levels)

Before any numeric level is frozen — and with **no solver invoked** — each of
the 60 `(seed, n_trips, b, setting)` instances is built by the generator and
subjected to closed-form **necessary** screens computed from instance fields
only (trip energies, deadhead energies, slot length, battery, charging power,
dwell windows). These are necessary conditions, not a feasibility proof; the
A2/dictator solves in the (future, reviewed) run are the actual feasibility
tests.

Feasibility necessary conditions (all must hold):

1. **Reachability / per-trip energy:** every trip's service energy plus the
   worst required deadhead is within the usable battery band
   `[soc_min, battery]`.
2. **Recharge headroom:** the maximum energy chargeable in the available depot
   dwell windows at `charge_power_kw` (`power × dwell_minutes / 60`, summed over
   depot dwells consistent with the timetable) is at least the per-vehicle net
   daily energy deficit implied by `battery`, `soc0`, and `soc_end`.
3. **Terminal-SOC admissibility:** `soc_end ≤ battery` and `soc_min ≤ soc_end`.

Relevance necessary conditions (all must hold, so charging is materially
price-responsive — otherwise B3 is not exercised):

4. **Charging is mandatory:** usable battery is strictly less than the
   per-vehicle service-plus-deadhead energy, so at least one midday depot
   charge is forced (a battery so large that no charging is ever needed makes
   the uplift price-insensitive and is out of scope).
5. **Charging is schedulable with slack, not saturated:** required charging
   fits within dwell windows with a nonzero, bounded margin (neither zero slack,
   which is fragile, nor unbounded slack, which is trivial).

Screen outcomes (generator-only, deterministic):

- If all 60 instances pass, the candidate levels are **frozen** and recorded in
  the manifest of Section 7. Freezing is a one-way step.
- If any instance fails, the level under test is adjusted **within a
  preregistered search rule** (bisection of the candidate toward baseline for
  feasibility failures; away from baseline for relevance failures), the screen
  is re-run, and freezing occurs only once all 60 pass. Because the screen reads
  no outcome, this adjustment introduces no look-ahead bias.
- If no level in the preregistered search band satisfies both feasibility and
  relevance for a factor, that factor is declared **not exercisable** on this
  grid and the pilot is revised before preregistration is finalized (a
  documentation event, not a run).

## 5. Measurement

For each of the 60 cells (in the future, reviewed run): solve the dictator
independently (adaptive, `tol_d`), then run A2 certified CG with `z_D_ub`
feeding the interval, exactly as the existing pilot does. Record the certified
`uplift_interval = [U_lo, U_hi]` per cell.

**Matched factor-minus-baseline interval effects.** For each base instance
`(seed, n, b)` and factor setting `f ∈ {S1,S2,S3,S4}`, the effect versus the
same-instance baseline `S0` is the rigorous interval difference

```
Delta_f = U_f - U_0 = [ U_f_lo - U_0_hi ,  U_f_hi - U_0_lo ].
```

Matching is on the base-instance identity; the two cells differ only in the one
screened physical factor. Both absolute effects (SEK) and, as a secondary
readout, relative effects `U / z_CH` are reported, with the certified interval
carried through all arithmetic. No effect is ever reported as a point.

## 6. Preregistered hypotheses and go / kill rules

Hypotheses (directional, fixed before any outcome):

- **H1 (battery):** tightening the battery (`S1`) does not decrease the internal
  uplift; loosening it (`S2`) does not increase it.
- **H2 (power):** lowering charging power (`S3`) does not decrease the internal
  uplift; raising it (`S4`) does not increase it.

Decision rules (evaluated only after the run and only on the certified
intervals; one look, no iteration):

- **GO to confirmation** iff *all* of:
  - (G1) the generator-only screen passed for all 60 cells at frozen levels;
  - (G2) every A2 cell certified within budget (`gap ≤ epsilon`) and every
    paired dictator converged (`adaptive_gap ≤ tol_d`) with valid replay — i.e.
    all 60 uplift intervals are certified and finite; and
  - (G3) at least one factor shows a **sign-consistent, zero-excluding matched
    effect** — `Delta_f` excludes 0 with a common sign — on a preregistered
    supermajority of **≥ 9 of the 12** matched base instances for one of its two
    settings.
- **KILL / revise** if any of:
  - (K1) the screen cannot be satisfied for a factor within its search band
    (Section 4) — that factor is not exercisable on this grid;
  - (K2) any cell fails to certify or converge, or fails replay validation —
    the population is not scoreable and the cell is a repair trigger, never a
    silent drop;
  - (K3) no factor meets G3 — the physical factors do not move the certified
    uplift in this regime (a real, publishable null for the atlas);
  - (K4) certified interval widths are too large to resolve the effects
    (median `|U_hi − U_lo|` exceeds a preregistered resolution bound relative to
    the median `Delta_f` magnitude) — the pilot is underpowered and tolerances
    must be tightened before any confirmation.

The GO/KILL outcome is itself a preregistered scientific result; a KILL is not
a failure to be re-rolled.

## 7. Provenance and reproducibility requirements

Any future run implementing this spec must, before scoring:

- Freeze and record, in a manifest with a SHA-256 over its exact bytes: the
  five settings' numeric `battery_kwh` / `charge_power_kw`, all held-fixed
  generator arguments, the seed/`n`/`b` grid, `epsilon`, `budget`, `tol_d`, the
  solver identity (backend + MIP gap), and the load-reconstruction policy
  version.
- Record the exact `Instance.hash()` for all 60 instances and the market hash
  for all 60 cells; the 12 baseline instances must be bit-identical to the
  same-seed/`n`/`b` `S0` cells.
- Hash all inputs and regenerate the screen and (later) the analysis
  **byte-identically** on re-run; the generator-only screen must be a pure
  function of the frozen manifest.
- Carry the certified interval endpoints, both certificates' gaps, and the
  visible PWL slack in every emitted record; never substitute a point estimate.
- Record the exact counts of Section 3 and assert them in the analyzer
  (`60` A2 cells, `60` dictator solves, `12` baselines, `48` matched effects).
- Bind the pilot's git commit and preregistration document hash into the
  emitted artifacts.

These requirements mirror the discipline already enforced for the closeout
ledger and the retrospective baseline; this draft does not implement them.

## 8. Separate fresh-seed confirmation stage

The development grid `{0, 11, 15}` is for *design and calibration only*. A GO
decision authorizes a **single, separate confirmation run on fresh seeds**:

- a preregistered set of confirmation seeds drawn from a range **disjoint from
  the development seeds `{0,11,15}` and from the reserved `16–31` band**, fixed
  in the preregistration before the confirmation run;
- the identical five screened/frozen settings, the identical `n`/`b` grid,
  method A2 only, identical tolerances and exact-count assertions;
- the generator-only screen (Section 4) re-applied to the fresh instances at the
  already-frozen levels (levels are not re-tuned on confirmation);
- one look: the GO factor's matched effect must **replicate** — same sign,
  zero-excluding, on the preregistered supermajority — for the pilot to
  graduate. No iteration, no level changes, no second look.

Only a passed confirmation stage justifies proposing any larger or cluster-scale
B3 factor campaign; that proposal is a later, separate document.

## 9. Boundaries and non-goals

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

## 10. Open questions for reviewers

1. Are OFAT contrasts sufficient for the atlas, or is a later full battery ×
   power grid required (at a larger, separately proposed cell budget)?
2. Are the candidate level ranges (Section 2.1) and the screen's search band
   (Section 4) appropriate, or should physical realism bound them differently?
3. Is the `≥ 9/12` supermajority (G3) and the resolution bound (K4) the right
   preregistered thresholds given the `epsilon + tol_d` interval widths?
4. Should the fresh-seed confirmation set size exceed 12 base instances to
   raise replication power before any cluster-scale proposal?
