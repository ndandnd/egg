# LLM handoff: `egg` price-maker EV fleet research program

Audience: a new LLM or human collaborator with no prior chat context.

Snapshot date: 2026-08-20 (America/New_York).

This file is a current operational/research handoff, not a replacement for the
repository's canonical specifications. When it conflicts with a committed
specification, result manifest, decision log, or live Git state, stop and
resolve the conflict from primary evidence before acting.

The filename carries the date this file was created, not the date it is
current to. **Currency: 2026-08-21, late.** Read the status board immediately
below before anything else; it supersedes any older statement further down.

---

# STATUS BOARD — 2026-08-21

## The one-line state

The flagship B3 factor pilot population is **complete and audited (PASS)**, its
analyzer is **verified clean across four independent review rounds**, and the
preregistered decision has **not yet been generated**. Generating and freezing
that decision is the entire critical path. Nothing else is close in value.

## What is working / resolved

| Item | State |
| --- | --- |
| B3 factor pilot population | **Complete.** All 60 Slurm tasks `COMPLETED 0:0`; audit PASS with 60/60 certified A2 cells, 60/60 converged dictators, 12 cells per setting, Gurobi backend, screen SHA `27c04d82…`, run manifest `9f7529fc…` |
| Pre-analysis integrity anchor | **Captured while outcome-blind.** `tree_sha256 efc5ca31…ace4`, 363 files, 60 dirs, 17385781 bytes. Now a frozen constant enforced by both analyzer and selector |
| Continuous integration | **Exists and is merged** (PR #43). Any branch that merges current main gets a machine-verified test count. Self-reported counts are no longer acceptable |
| PR #37 closeout tooling | **Rule and anchor verified; NOT yet mergeable.** `0af91df`, 802 CI-green tests, four review rounds. A fifth review found two remaining blockers (shape-only `run_commit`; scoring the live tree before freezing the snapshot it binds). See §17.12 |
| The population's actual provenance | **Verified by hand:** `run_commit = 5b63e72` resolves to a real commit object and is an ancestor of `main`. So the shape-only check is a hygiene gap for *future* manifests, not an exposure for this population — which is additionally protected because `MANIFEST.json` is one of the 363 anchored files |
| Novelty claim | **No collision found in the 2026-08-20 sweep.** Canonical ingestion into `papers.csv`, dimensional scoring, and full-text verification all remain pending. Do not write "re-verified" — the sweep was abstract-level |
| Scaglione positioning | **Resolved.** She is our coauthor; `yao2025` is a coordination bridge, not a threat |
| Seed-collision worry | **Resolved.** Every egg Slurm job name is prefixed `egg-`; none of the ~90 running jobs match, so they belong to the adjacent project. Reserved seeds 32–47 are safe |
| Cursor identity gate | **Resolved.** `gh api user` always 403s for Cursor's GitHub App token; that is expected, not an authorization failure. Working gate is remote-URL check + `git push --dry-run`, with authorship from `git config` |

## What is open, in priority order

1. **Repair PR #37, then have a *different* reviewer clear it.** Two blockers:
   `run_commit` accepted on shape alone, and the analyzer scores the live tree
   before freezing the snapshot it later binds. Both are closable without
   touching the scientific rule. **The B3 decision freeze waits on this.**
2. **Repair PR #45, then re-review it.** Three criticals; it must not launch
   anything until repaired *and* independently re-reviewed. Seeds 32–37 are a
   one-shot resource.
3. **Harden PR #47.** It fixes the output-path hazard, but an independent test
   drove `EGG_PYTHON=/usr/bin/true` plus `EGG_ENV_SCRIPT=/dev/null` to make the
   real submit script exit 0 while producing no evidence. See §17.12 for what
   is a #47 regression versus what is pre-existing.
4. **Write and freeze a replication comparator** *before* any replication runs.
   "Certified intervals agree within tolerance" is currently prose. Without a
   frozen rule — which cells, which fields, what tolerance, what counts as
   agreement, what a single disagreement triggers — a disagreement can be
   rationalized after it is seen. This is the same preregistration logic
   applied everywhere else in the program.
5. **Then freeze the B3 decision** (merge repaired #37 → pull → rerun the newly
   merged audit **read-only, without `--out`** → verify the anchor immediately
   before and after scoring → run the analysis → read `boundary_adjacent` →
   freeze → commit).
6. **Close the A6 holdout.** Its raw run from job `248911` already exists; only
   the one-shot `recover2-pack` publication stands between it and a scoreable
   adoption-gate result. Zero cluster cost, and it should be attended. Have an
   agent produce (not execute) one read-only preflight plus one exact operator
   command first.
7. **Laboratory PRs: do not merge yet.** #38, #41, and #42 have **no CI on
   their exact heads** (verified). #39 is CI-green but main should stay stable
   until the decision is frozen. #46 is **parked** — see §17.12.
6. **Research work needing no cluster:** the cite-and-scope pass into
   `papers.csv`/novelty matrix; the OMIE market-calibration spike (exploratory,
   see §16.3 corrections); ML stages 2–4 (dataset builder, training, evaluation
   harness with its preregistered kill baseline).

## Do not do

- Do not launch the confirmation until #45 is repaired and re-reviewed.
- Do not launch or re-run the pilot until the submit-script output-path hazard
  (§17.7) is fixed — the array would write into the audited tree.
- Do not merge or pull on Unicorn while an egg array is running (§17.10 item 6).
- Do not accept an agent's self-reported test count, or let a PR's author
  review it.
- Do not launch the paused A1 grid, the 960-cell campaign, a scale study, or
  the ML data campaign to fill idle capacity.

## Current PR board

`main` = `ed8b06f3d7e8e4a7ecc5fbfd74ff0b819ac24fa4`. Nothing below is merged.

| PR | Head | State |
| --- | --- | --- |
| #37 | `0af91df` | **Repair before merging.** Rule + anchor verified over four rounds, 802 CI tests, but two blockers remain (§17.12) |
| #47 | `ef95127` | **Harden before merging.** Output-path fix is correct (diff reviewed line by line, 721 CI tests) but an rc=0/no-evidence bypass was demonstrated (§17.12) |
| #45 | `da2cdb6` | **Blocked.** 3 criticals + 3 highs; repair brief written |
| #46 | `f709165` | **PARKED.** CI-green but reported not launch-ready: per-call rather than per-cell wall cap, replay-flag alignment, dual-spread across slots, and no encoding of the price trajectory it claims to learn (§17.12) |
| #44 | `c5c3aac` | Research candidate inbox (notes only), CI-green |
| #42 | `7b8fce1` | Column proposer lab; protocol violations reverted — **no CI on this head** |
| #41 | `3745c43` | GIRO frozen loader — clean diff, but **no CI on this head**; merge nothing without a machine-verified run |
| #40 | `71468ed` | Uplift settlement; regret extension **not yet done** |
| #39 | `2ad05f5` | Two-cycle witness, repaired, CI passes |
| #38 | `1ae553f` | Branch-and-price lab, hardened — **no CI on this head** |
| #32 | `8d498b8` | B31 corpus builder, merged with main, later/optional |
| #29 | `c32056a` | Cloud agent environment, low priority |

## Task-brief inventory (these are agent prompts, not status documents)

Consumed — do not re-paste: `BNP_DICTATOR` (→#38), `B1_MINIMAL_CYCLE` (→#39),
`UPLIFT_SETTLEMENT` (→#40), `FROZEN_LOADER` (→#41), `COLUMN_PROPOSER` (→#42),
`CI` (→#43, merged), `REVIEW_PR37`, `REPAIR_PR37`, `REVIEW3_PR37`,
`REPAIR2_PR37` (→`0af91df`), `REPAIR_PR38`, `REPAIR_PR39`, `REPAIR_PR42`,
`CONFIRM_DRIVER` (→#45), `ML_DATA_DRIVER` (→#46).

**Still to be handed out:**

- `CURSOR_HANDOFF_REPAIR_PR45_20260821.md` — the three criticals. Highest
  priority brief.
- `CURSOR_HANDOFF_SUBMIT_OUT_FIX_20260821.md` — no PR yet; unblocks replication.
- `CURSOR_HANDOFF_EXTEND_PR40_REGRET_20260820.md` — never picked up; #40's head
  is unchanged.

Pre-existing briefs from before this session (`B3_BASELINE_20260819`,
`PHASE012_20260814`, `PR28_FINAL_CLOSEOUT_20260819`) are historical.

## Where the detail lives

Sections 1–7 are the unchanged science. Sections 8–15 are the experiment
specifications and program plan. Section 16 is the 2026-08-20 research sweep
(novelty verdicts, market calibration with its corrections, the ML design
contract, venue fit). Section 17 is the chronological operator log for this
campaign — audit PASS, the anchor, the review rounds, the hazards, and the
adopted operating habits. When section 17 conflicts with an earlier section,
section 17 and this board win.

---

## 0. Read this first

The repository is public: <https://github.com/ndandnd/egg>.

Revision note: this file was written on 2026-08-20 morning and substantially
updated the same day (late), after a large Cursor engineering round, a
six-agent literature sweep, and a fresh `squeue` observation. Sections 1-7
(the science) are unchanged; sections 0, 8.3, 9, 11-16 are current as of the
update.

The live remote `main` was verified at update time as:

```text
ed8b06f3d7e8e4a7ecc5fbfd74ff0b819ac24fa4
```

This is `5b63e725d0fd85cfb0b83f462a612016e7f4321a` (PR #36, the B3 factor
pilot launcher) plus the merge of PR #43, which added the repository's first
CI: a CBC-only GitHub Actions test gate. Every PR branch that merges current
main now gets a machine-verified test count instead of an agent-self-reported
one. **Do not accept a self-reported test count from any agent again.**

The most important live fact concerns the 60-cell B3 factor pilot, which had
been running on Cornell's Unicorn cluster as Slurm array job `311153`. In an
operator `squeue` dump taken at update time, **`311153` no longer appears**.
Roughly 70 other `nc437` jobs were running (job names `ll_CG_k3`, `p240_k08`,
`p240_k13`, `c240_k08`, `c240_k13`, `c240_k20`, `cpi_k20s`, `cpi_k30s`,
`cpi_k40c`, `wp_k20_s`, `wp_k30_s`, `wp_k40_s`; array `290572` plus job ids in
the `3104xx-3109xx` range, all lower than `311153`).

Two things follow, and neither may be skipped:

1. **The B3 array is very probably finished, but an empty `squeue` is not
   evidence of a completed population.** The handoff rule stands: verify 60
   checkpoints, 60 cell identities, 60 converged dictators, 60 `done` and
   certified A2 states, and Slurm task-level completion (`sacct`), then run the
   merged hardened audit. If any cell is missing or failed, that is an
   engineering incident to preserve and diagnose — never a partial population
   to score.
2. **Those other jobs are NOT from this repository — resolved 2026-08-21.**
   Every Slurm job name defined anywhere in `src/cluster/*.sub` on main is
   prefixed `egg-` (`egg-b3-factor-pilot`, `egg-a6-holdout`, `egg-b2a2-pilot`,
   `egg-audit`, `egg-phase1`, and so on). The names seen in `squeue`
   (`cpi_k20s`, `wp_k20_s`, `ft_k08_s`, `fx_k20_s`, `b4_k30_r`, `ch_b4_k4`,
   `ll_CG_k3`, `p240_k13`, `c240_k20`, and the `ch_*` family in the
   `scaglione` partition) match none of them, and the `b4_*` -> `ch_b4_*`
   dependency chain is a two-stage pipeline `egg` does not have. They belong to
   an adjacent project (EVSP-DR or the microgrid work).

   Consequence that matters: **there is no seed-collision risk** between those
   jobs and `egg`'s reserved ranges (16-31 A6, 32-37 B3 confirmation, 38-47
   reserved), because they are a different codebase with different seed
   semantics. Do not cancel them; they are someone's — probably your own —
   other research. Note that job names can be overridden on the `sbatch`
   command line, so if a future `squeue` shows an unprefixed name that *does*
   look like `egg` work, re-check rather than assuming.

Immediate scientific order:

1. Verify B3 population completeness properly (above), then run the exact
   hardened audit on all 60 cells.
2. Generate the preregistered B3 analysis from one reviewed code commit. The
   candidate analyzer is PR #37, which has now been through two independent
   adversarial reviews and one full repair round; it needs a third independent
   review before it is trusted to produce the decision (see section 12).
3. Freeze and commit the pilot decision before building or launching any
   fresh-seed confirmation.
4. In parallel, complete the separate A6 holdout recovery/package closeout;
   its scientific result is still unscored.
5. Only after the B3 decision is frozen should any new cluster campaign be
   considered, including the ML data-generation campaign described in
   section 16. Available compute is still not a decision rule.

## 1. What this project is

`egg` is a PhD-thesis research repository about price formation for
indivisible mobile flexibility, centered on a price-making electric vehicle
scheduling problem (EVSP).

The classical EVSP assigns vehicles to mandatory timetabled trips, constructs
complete vehicle duties, and chooses charging subject to compatibility and
battery state of charge. Classical formulations treat electricity prices as
exogenous. Here the fleet is large enough that its charging load changes the
price it faces:

```text
posted price -> optimal trip-covering schedule and charging load
             -> market price changes -> fleet responds again
```

This is the project's “chicken-and-egg” loop. The working umbrella title is:

> Price formation for indivisible mobile flexibility: from benevolent
> dictator to market.

The research goal is not merely to show that prices and charging interact.
That is well occupied in the literature. The intended contribution is the
combination of:

- mandatory, indivisible, trip-covering fleet duties;
- endogenous/shared price formation caused by the fleet's own load;
- exact or certificate-bearing optimization and best-response logic;
- economically defensible coordination, settlement, and uplift accounting.

The current flagship is the Chapter I package B1+B2+B3:

- **B1:** interpret naive price iteration as unstabilized decomposition and
  characterize cycling at the kinks of an integer fleet response;
- **B2:** replace memoryless price iteration with certified column-generation
  negotiation/stabilization;
- **B3:** measure the internal uplift caused by indivisibility, using certified
  bounds on the dictator and convex-hull problems.

## 2. Project boundary and inherited assets

This is a separate project, not a rename of EVSP-DR.

Two adjacent projects are provenance and reusable oracles:

1. **EVSP-DR**: exact price-taking EVSP work on Swedish/Partille bus data,
   including column generation, SOC-aware pricing, route re-realization, and
   restricted-master MIP machinery.
2. **`evspv2g_dp` / Cho-Lodi-Scaglione microgrid work**: the benevolent
   dictator endpoint, co-optimizing fleet operations, charging/V2G, storage,
   solar, and generation.

The thesis studies the economic/computational space between the price-taker
and dictator endpoints. Do not copy adjacent repositories wholesale. Call or
adapt them as explicitly versioned oracles. In particular, old EVSP-DR route
identities may collapse distinct charging realizations; a route cannot simply
be re-costed under a new tariff without re-realizing charging or using an
exact pricing path that preserves the needed realization detail.

## 3. Mathematical/economic objects

### 3.1 Fleet response

At posted price vector `p`, the fleet value function has the form

```text
V(p) = min over feasible complete schedules S of c(S) + p · e(S).
```

It is concave and piecewise linear in `p`. Aggregate load is a supergradient.
Because schedules/duties are indivisible, the response jumps at kinks. These
jumps are the source of two-cycles, long damped orbits, discontinuous welfare,
and nonzero uplift.

### 3.2 Market model used in the synthetic laboratory

The current synthetic market is slotwise affine:

```text
p_t = a_t + b_t (U_t + L_t),
```

where `U_t` is background/uncontrolled demand and `L_t` is fleet load. The
base-price shape is “duck”-shaped. This is a stylized inverse supply/price
curve, not a solar-generation model.

### 3.3 Four economic regimes

Keep these separate:

- **uncontrolled:** a flat-price/operational schedule followed by a simple
  charge-on-arrival policy;
- **price taker:** minimizes its bill at posted prices but ignores its effect
  on those prices;
- **strategic price maker:** anticipates its own price impact (a monopsony-like
  marginal-outlay response);
- **benevolent dictator/planner:** minimizes true integrated system cost.

### 3.4 Certified B2/B3 quantities

- `z_D`: the integer benevolent-dictator optimum (held as a certified
  lower/upper interval in computation).
- `z_CH`: the convex-hull/schedule-column master optimum certified by column
  generation.
- **internal uplift:** `z_D - z_CH`, the nonconvexity/indivisibility gap that
  prevents pure linear prices from fully supporting the integer solution.

Do not confuse this B3 uplift with the compact vehicle-indexed MILP's root-LP
gap. The latter is formulation-specific and only motivates B3.

## 4. Literature and novelty status

The broad initial literature search is complete, but manuscript-grade
verification is not.

The current committed `ref/papers.csv` contains **322** unique works:

- 17 audited at full text;
- 270 abstract-level;
- 35 institutional/grey;
- relevance: 77 core threats, 109 method anchors, 136 domain context.

Older chat/report language sometimes said 323/271/137. The live committed CSV
at `main = 5b63e72` is the authority for the counts above. Preserve this
discrepancy rather than silently repeating the older number.

The brainstorm now spans B1-B39. The novelty matrix reports no identified work
occupying the full combination of exact trip-covering duties, endogenous
prices, and exact/certificate-bearing solution logic. However, generic
price-load feedback, price-maker bidding, storage games, fixed-point
price-route loops, uplift/VCG settlements, and route-response learning are
already occupied. Never claim “first price-making EV fleet” or “first EVSP
whose cost depends on its own load.” The defensible claim is narrower:

> an exact trip-covering scheduled fleet embedded in shared price formation,
> with certificate-bearing coordination and settlement logic.

Before drafting a paper, complete the flagship-specific forward/backward
citation sweep and full-text audit the gating queue, especially the work by
Yao/Scaglione, Najafi-Fripp, Andrianesis et al., du Merle, Briant, O'Neill,
Gribik/Hogan/Pope, and the most relevant stabilized-CG and nonconvex-pricing
papers. Coordinate positioning with Anna Scaglione because the closest
logistics/LMP fixed-point work includes her as a coauthor.

A six-agent web sweep on 2026-08-20 (late) re-verified the novelty claim
against this baseline and found it still standing; see section 16 and
`ref/review_notes/DEEP_RESEARCH_20260820.md`. That sweep also settled a
framing point that earlier language got wrong: Anna Scaglione is **our
coauthor**, so `yao2025` (arXiv:2505.04532, now listed for IEEE CDC 2025) is a
coordination bridge and the nearest neighbor to cite, not an adversarial
threat. Position the two papers jointly with her.

Canonical literature files:

- `ref/papers.csv`
- `ref/LITERATURE_INDEX.md`
- `ref/NOVELTY_MATRIX.md`
- `ref/READING_QUEUE.md`
- `ref/BRAINSTORM_20260814.md`
- `ref/RESEARCH_DIRECTIONS.md`
- `ref/review_notes/`
- `ref/review_notes/DEEP_RESEARCH_20260820.md` (new; abstract-level
  confidence, committed on branch `research/deep-research-20260820` as draft
  PR #44)

## 5. Research program and priorities

The recommended thesis arc is:

1. **Computation:** decomposition as price formation, cycling/stabilization,
   certified convex-hull negotiation, and internal uplift.
2. **Economics:** the four-regime welfare ladder, price-taking distortion,
   discrete monopsony, and integrality-related fixed-point existence.
3. **Mechanisms:** convex-hull/two-part settlements, minimum uplift, feasible
   duty menus as exclusive-group bids, and exact deviation separation.
4. **Technology:** V2G, locational prices, energy deadheading/virtual
   transmission, reserves, and resilience.
5. **Later/cross-cutting:** switch-boundary learning and multi-fleet integer
   programming games.

The lowest-hanging current research is B3, not machine learning:

- certified uplift is already visible in the B2 population;
- the factor pilot is testing whether battery and charging power explain it;
- the required methods already exist and are certificate-bearing.

Naive iterative EVSP + price/demand forecasting is no longer the primary
algorithmic direction because the measurement campaign showed that the
memoryless loop cycles widely. Learning routes/switches remains promising but
must be economically filtered: raw schedule hashes are dominated by
alternative-optimum/degeneracy noise. Learning should accelerate proposal or
sampling while the exact oracle remains the feasibility/certification
backstop.

## 6. Code and evidence architecture

The main code is under `src/`:

```text
src/egglab/
  instance.py     synthetic EVSP generator; frozen-data loader stub
  market.py       affine endogenous-price market and welfare accounting
  solver.py       python-mip backend; Gurobi required for cluster evidence
  evsp.py         EVSP MILP oracle and independent physical replay
  regimes.py      uncontrolled/taker/strategic/dictator solves
  loops.py        price iteration, fixed-point and cycle detection
  boundary.py     switch-boundary sweeps and economic filtering
  b2a2.py         plain certified column generation (A2)
  b2a345.py       stabilized variants A3-A5
  a6.py           event-triggered sparse stabilization
  checkpoint.py   atomic, resumable checkpoints
  records.py      provenance/evidence schema

src/experiments/
  run_*.py        deterministic cell drivers
  audit_*.py      exact-count, replay, identity, and certification audits
  analyze_*.py    deterministic scientific artifacts
  package_a6_holdout.py
                  frozen-snapshot A6 pack/import/recovery workflow
  b3_factor_screen.py
  b3_factor_pilot.py
  run_b3_factor_pilot.py
  audit_b3_factor_pilot.py
  analyze_b3_factor_pilot.py

src/cluster/
  guarded Slurm launchers and submit scripts
```

Raw runs live under gitignored `src/runs/`. Curated tables, figures, summaries,
and manifests live under committed `result/`. Every accepted result should
carry exact input hashes, code commit, grid identity, solver identity,
certification status, and deterministic regeneration evidence.

Evidence labels are load-bearing:

- exact/certified solve;
- certified convex-hull interval;
- finite-pool or restricted-menu diagnostic;
- empirical synthetic finding;
- retrospective/exploratory restatement;
- unresolved transient;
- implementation incident (never scored).

Never promote one tier into another in prose.

## 7. Completed scientific evidence

### 7.1 Phase 0/1/2 synthetic closeout

Canonical analysis: `result/analysis/20260816T190835Z/` and
`doc/MEASUREMENT_RESULTS.md`.

Key certified synthetic findings:

- no feedback (`b=0`) gives the expected one-step fixed point;
- weak feedback (`b=0.002`) is mostly stable, with one observed rescue from
  damping;
- moderate/strong feedback largely destroys fixed points;
- at `b=0.05`, zero fixed points were observed across 176 tested baseline
  algorithm/parameter cells;
- all 49 undamped observed cycles had length exactly 2;
- damping changed short two-cycles into long orbits/unresolved transients
  (median cycle lengths 11-14, maximum 140), not reliable convergence;
- stability is strongly instance-dependent (seed 11 accounts for the
  moderate-feedback fixed points in the damping frontier);
- price-taking distortion grows sharply with price impact: at `b=0.05`, the
  mean/max taker-minus-dictator gaps were about 25.97/79.8;
- the strategist stayed within 3.74 of the dictator across the tested grid;
- 92 economically meaningful boundary switches were found in 43/64 sweeps:
  57 duty changes, 35 charging-only, zero fleet changes;
- median/max L1 load jump at economic switches was 35.5/195.8 kWh;
- 2,559 degenerate tie changes and 89 margin ties were excluded, so learning
  raw schedule hashes without filtering would mostly learn solver selection
  noise.

All of these are synthetic-laboratory results. No real-data external-validity
claim has been established.

### 7.2 B2 certified negotiation experiment

Algorithms:

- A0: undamped tatonnement label;
- A1: constant-damping family (large comparison campaign paused);
- A2: plain certified column generation;
- A3: du Merle-style stabilization;
- A4: Wentges smoothing;
- A5: proximal/bundle stabilization;
- A6: sparse event-triggered use of clean and candidate calls.

Canonical B2 full-population artifact:
`result/b2_full/20260818T140356Z/`.

Population: 64 matched instances per method, 256 A2-A5 method-cells. All
256 certified within the 240-call budget.

Median total oracle calls:

```text
A2 24, A3 30, A5 32, A4 34.
```

Median clean calls:

```text
A2 24, A3 16, A5 17, A4 18.
```

Conclusion: the stabilized variants substantially reduce clean calls but add
too many candidate calls to improve total calls at `n in {8,12}`, `T=28`.
The preregistered 2x improvement gate failed and the plain A2 kill signal was
active. This rejects the current A3-A5 implementations as end-to-end speedups;
it does **not** show that stabilization has no mechanism or value. A2 itself
is already a successful certified alternative to tatonnement.

### 7.3 A6 sparse-stabilization line

A6 tries to retain the clean-call advantage while spending exactly one oracle
call per master iteration, choosing clean versus stabilized candidate calls
by a frozen trigger priority. Certification remains based only on clean-master
upper bounds and clean-dual lower bounds.

Burned pilot:

- 24/24 cells certified;
- 12 `a6_a3` and 12 `a6_a4` cells;
- `a6_a3` won only 2/12 under the frozen selection rule;
- `a6_a4` is therefore the sole holdout arm.

Canonical selection:
`result/a6_pilot/20260819T005514Z/SELECTION.json`.

The first holdout attempt, job `218143`, was an implementation incident:
126/128 tasks completed and two matched cells failed because a tiny negative
raw aggregate-load residual was stored as a nonphysical master-column load.
It is permanently unscored.

A full replacement holdout was run as job `248911` on the same frozen
population (A2 + `a6_a4`, seeds 16-31, `n={8,12}`, `b={0.01,0.05}`, 128
cells). The raw run exists on Unicorn, but its scientific result has **not**
been accepted or scored. Packaging/validation encountered two successive
numerical-validation incidents:

- EI-026: inconsistent tolerance scales rejected a within-scale negative
  reconstructed pricing gap;
- EI-027: the physical-incumbent reconstruction adjustment exceeded the
  earlier operand-only tolerance, requiring a physical-bridge allowance.

Reviewed fixes and a one-shot second-stage recovery path are merged through
PR #35. At the last observation, Unicorn contained:

```text
src/runs/a6_holdout.CLOSEOUT_CLAIM.json
  sha256 1b0acf0b8232d4b08e764564e2732fcfa9c28dd53456a1415085b77cb38f6675

src/runs/a6_holdout.RECOVERY_CLAIM.json
  sha256 88c22f06ce6bc8dcff56c0d6737c91bbd39fe8da79c2b6ba6d2a987b6b6abe88
```

No successful second-stage `recover2-pack` publication had been reported.
The next agent must inspect the current merged `package_a6_holdout.py`, the
claim files, `doc/UNICORN_RUNBOOK.md`, and the incident ledger before issuing
an operator command. Do not invent a recovery command and do not create a
third recovery stage.

### 7.4 B3 certified-uplift baseline

Canonical artifact: `result/b3_baseline/20260820T025758Z/`.

This is a no-solver, retrospective/exploratory restatement of the B2
population, one A2 interval per 64 unique instances, with A3-A5 used as
consistency witnesses.

Results:

- 38/64 intervals certify strictly positive uplift;
- 21 strict zero crossings;
- 5 exact-zero boundaries;
- all 64 four-way A2-A5 interval intersections are nonempty;
- feedback contrast: 23/32 positive, 1 negative, 8 unresolved;
- workload contrast: 19/32 positive, 6 negative, 7 unresolved;
- the strongest stratum was `n=12, b=0.05`: 13/16 positive, median interval
  approximately `[3.5795, 3.5901]`.

Interpretation: there is a real certified synthetic uplift signal, but matched
effects are heterogeneous. Intervals containing zero do not establish absent
uplift; they establish non-resolution at the current tolerances.

## 8. Current B3 factor pilot

### 8.1 Why this experiment exists

The B3 baseline held battery capacity and charge power fixed. The factor pilot
tests whether tighter/looser physical flexibility changes internal uplift.

The design is one-factor-at-a-time around a common baseline:

| setting | battery kWh | charge kW | preregistered direction |
| --- | ---: | ---: | --- |
| `S0_baseline` | 60 | 150 | reference |
| `S1_batt_low` | 45 | 150 | non-negative effect |
| `S2_batt_high` | 90 | 150 | non-positive effect |
| `S3_pow_low` | 60 | 75 | non-negative effect |
| `S4_pow_high` | 60 | 300 | non-positive effect |

The levels were frozen by a deterministic, solver-free feasibility/relevance
screen. Canonical screen artifact:
`result/b3_factor_screen/20260820T105318Z/`; screen record SHA-256:
`27c04d82bc88b62eed84394569b3ab8a35238a3a57c9cf4ba6463fb85f7bf603`.

The pilot population is exactly:

```text
settings: 5
burned development seeds: {0, 11, 15}
n_trips: {8, 12}
b: {0.01, 0.05}
A2 method-cells: 60
independent dictators: 60
matched factor-minus-baseline contrasts: 48
epsilon = 0.01, tol_d = 0.01, budget = 240
Gurobi only
```

Hard boundaries:

- no A6 code or data;
- no seeds 16-31;
- no fresh confirmation seeds 32-37 during the pilot;
- every cell is bound to the frozen screen, run commit, run-manifest SHA,
  instance hash, market hash, and solver identity.

The merged launcher submits the 60-cell array held, atomically binds `JOB.json`
to the run manifest, and only then releases the job. Bind or release failure
cancels the exact held job. Concurrency is capped at 12.

### 8.2 Preregistered decision

For each of the four factor settings, compute 12 matched interval contrasts
against S0. Apply the setting's frozen direction sign. Select `f*`
deterministically by highest direction-consistent zero-excluding count, then
larger direction-signed median midpoint, then fixed factor order.

- `UNDER-RESOLVED` if `abs(median) <= 0.04`;
- `GO` if signed median `> 0.04` and count `>= 9/12`;
- otherwise `NO-GO`;
- any incomplete/invalid population is `INVALID/HALT`, not a scientific null.

If and only if GO is frozen in a committed selection artifact, the separate
confirmation population is:

```text
seeds {32,33,34,35,36,37}
S0 versus selected factor only
n {8,12}
b {0.01,0.05}
24 matched contrasts = 48 method-cells
confirmation gate: >=18/24 direction-consistent zero-excluding
                   and signed median > 0.04
```

There is no confirmation launch authorized yet.

### 8.3 The closeout tooling: PR #37 (delivered, reviewed twice, repaired)

The outcome-blind closeout task did return, as draft PR #37 on branch
`cursor/b3-pilot-closeout-5fa0`: the evidence-complete analyzer, an immutable
confirmation-selection freeze tool, and a B3 pack/import utility.

Two **independent** adversarial reviews (different agents, neither the author)
found the PR unsafe to merge. They converged on the same class of defect and
each built working forgeries:

- the selector trusted `DECISION.json`'s self-reported state, so an
  `UNDER-RESOLVED` analysis could be edited into a `GO` authorization by
  changing state/count/median and rehashing;
- the analyzer trusted stored certificate summaries, so edited CH histories
  produced a fabricated 12/12 GO while the underlying solver evidence was
  untouched, and `adaptive_converged` was believed without checking
  `z_d_ub - z_d_lb <= tol_d`, replay validity, or solver identity;
- import accepted arbitrary self-described trees (empty `runs/`, empty
  `analysis/`, `cells: {}`), and packaging bound only the shared design
  manifest, so one job's raw results could be packaged with another job's GO
  analysis.

All 17 findings were repaired in four ordered commits, head
`8144483eb292686477d0c24d2a12aa959e10a6f3`, with every reproduction committed
as a regression: the selector now recomputes the entire preregistered decision
from the primitive tables and requires exact agreement with `DECISION.json`,
`MANIFEST.json["decision"]`, and `setting_summary.csv`; the analyzer replays
`lb_best`/`ub_ch` from chronological event logs and recomputes dictator
certificates; the packager freezes one inventory, records a `raw_binding`
(raw-tree digest + Slurm job id + `JOB.json` hash) that pack and import both
require, and re-verifies quiescence immediately before the rename; boundary
tests are pinned float-exactly at median ±0.04 and count 9-vs-8.

The repair agent recorded four reasoned disagreements (`os.link` rather than
`rename` to honor no-replace; incomplete marker plus positive completion
record; the acknowledged limit that replay cannot catch a fully consistent
co-edit of the RMP side without re-solving; and INVALID/HALT analyses being
unpackable). Those are argued from spec text in the PR and should be reviewed
on their merits.

**This PR still needs a third independent review before it is used to produce
the pilot decision.** It is the code that decides GO / NO-GO / UNDER-RESOLVED
on the flagship experiment; two rounds of review found real forgeable paths,
which is exactly the reason not to trust round three's author either.

## 9. What to do next

### 9.1 First: verify live state

On any machine with GitHub access:

```bash
git ls-remote https://github.com/ndandnd/egg.git refs/heads/main
```

Expected at this update: `ed8b06f3d7e8e4a7ecc5fbfd74ff0b819ac24fa4`.
If it advanced, inspect the intervening commits/PRs before using this handoff.

On an existing interactive Unicorn login prompt, wrap guarded blocks in a
subshell so an error does not close the user's login session:

```bash
(
    cd "$HOME/egg/src" || exit 1
    export PATH="/usr/local/slurm/current/bin:$PATH"
    JOB_ID="$(python3 -c \
      'import json; print(json.load(open("runs/b3_factor_pilot/JOB.json"))["job_id"])')"
    squeue -r --jobs="$JOB_ID"
)
```

Never put a top-level `set -euo pipefail`/`exit` block into the user's current
interactive SSH shell. A prior command failure disconnected them. Use a
subshell `( ... )` for all future guarded Unicorn blocks.

Because `311153` has already left the queue, the queue check above is no
longer the operative test. Establish what actually happened to every task
with accounting rather than the live queue:

```bash
(
    cd "$HOME/egg/src" || exit 1
    export PATH="/usr/local/slurm/current/bin:$PATH"
    JOB_ID="$(python3 -c \
      'import json; print(json.load(open("runs/b3_factor_pilot/JOB.json"))["job_id"])')"
    sacct -j "$JOB_ID" --format=JobID,State,ExitCode,Elapsed,NodeList -P
)
```

Every one of the 60 array tasks must show `COMPLETED` with exit code `0:0`.
Any `FAILED`, `TIMEOUT`, `OUT_OF_MEMORY`, `CANCELLED`, or `NODE_FAIL` task is
an engineering incident: preserve the raw evidence, classify it, and do not
score the remaining cells.

### 9.2 When the B3 array is complete

Do not infer completion from an empty `squeue` alone. Verify 60 checkpoints,
60 identities, 60 converged dictators, 60 `done` A2 states, and Slurm task
completion. Then run the merged hardened audit:

```bash
(
    set -euo pipefail
    cd "$HOME/egg/src"
    export PATH="/usr/local/slurm/current/bin:$PATH"
    source cluster/unicorn_env.sh
    python experiments/audit_b3_factor_pilot.py \
        --runs runs/b3_factor_pilot \
        --out runs/b3_factor_pilot/AUDIT.md
)
```

If the audit fails, preserve all raw evidence, classify the failure as an
engineering incident, and do not score a subset. If it passes, choose the
canonical analyzer commit. That choice is now a real decision with a clear
recommendation: **PR #37's hardened analyzer, after a third independent
review and merge**, because the currently merged analyzer is the version whose
weaknesses two reviews demonstrated (stored-summary trust, unchecked dictator
convergence, no budget ceiling, impossible tightened intervals). Do not
generate the decision from merged-but-superseded code just because it is
already on main, and do not let the human-readable Slurm logs become the
scientific source of truth.

After analysis:

1. independently review tables/manifests and regenerate byte-for-byte;
2. commit the analysis artifact using the project's code-first/artifact-second
   provenance protocol;
3. freeze a machine-readable selection;
4. update `doc/DECISION_LOG.md` and `doc/RESEARCH_STATUS.md`;
5. only a committed GO authorizes confirmation implementation/launch.

### 9.3 Close the A6 holdout separately

Use the reviewed second-stage recovery path merged through PR #35. Verify the
two frozen prior claim SHA-256 values, raw-tree digest, Git ancestry, Slurm
quiescence, and absence of an existing package before consuming the one-shot
recovery. A6 and B3 must remain separate evidence streams.

The A6 adoption gate, once scoreable, is all of:

- selected A6 arm certifies at least 61/64;
- certification rate is at least A2's;
- median matched score ratio `<= 0.85`;
- at least 38/64 matched wins.

Any audit/validity failure halts unscored. A final negative ends the current
stabilization line absent new theory.

### 9.4 Scientific work that can proceed without more cluster data

- write/prove the B1 equivalence and minimal cycling example (a machine-checked
  strict two-cycle witness now exists in PR #39 — use it, do not redo it);
- formalize how integer response kinks relate to fixed-point existence;
- turn B2's negative total-call result into a careful mechanism/overhead
  story rather than a failed algorithm story, using the **scope correction**
  in section 16: the honest claim is that *dense iterative* stabilization
  loses end-to-end *at small n*;
- complete the flagship-specific full-text literature sweep, and fold the
  2026-08-20 sweep's new candidates into `ref/papers.csv` and the novelty
  matrix (the cite-and-scope pass, section 16);
- run the market-calibration spike: fit the affine slope `b_t` against real
  published aggregated bid curves (OMIE; free, verified, section 16). This
  single artifact upgrades the defensibility of every synthetic result and
  needs no cluster;
- build the ML dataset-builder / warm-start evaluation harness (section 16
  stages 2-4) as reviewed, adversarially tested, outcome-blind code;
- prepare the B3 factor-result table/figure plan outcome-blind;
- design the real-data GIRO validation only after the frozen subset and data
  manifest exist. PR #41 now provides the manifest-verified freeze/load
  machinery that makes that discipline checkable.

Do not launch the paused 576-cell A1 grid, the old 960-cell campaign, a scale
study, or a fresh-seed B3 confirmation merely to keep the cluster busy.
Available compute is not a scientific decision rule.

## 10. Known engineering lessons

The durable incident ledger is `doc/ENGINEERING_INCIDENTS.md`. Important
lessons include:

- reconstruct physical nonnegative load from charge events; do not trust tiny
  solver residuals in redundant aggregate variables;
- replay certificate logic from chronological events; do not trust stored
  summary labels or gaps;
- compare solver bounds/incumbents with one coherent operand-scaled tolerance
  and account explicitly for physical-objective reconstruction adjustments;
- bind every run to full commits, manifests, instance/market hashes, solver
  identity, Slurm lineage, and exact cell counts;
- package a frozen snapshot, not a live tree;
- use no-replace atomic publication and preserve incomplete incident evidence;
- separate code commits from generated artifact commits;
- never score partial populations after an implementation failure;
- never learn on raw schedule hashes without filtering alternative optima.

Some incident statuses remain `FOUND — IN PROGRESS` because the ledger uses a
merge/recovery discipline; inspect both current code and the status text.
EI-026/EI-027 remain operationally open until the actual A6 recovery package
successfully publishes and is validated.

## 11. Machines, paths, and Git hazards

There are two personal Macs plus Unicorn.

- One Mac (historically username `nadan`) has the authenticated path to
  Unicorn and a repo often located at
  `/Users/nadan/Documents/projects/egg`.
- The Mac on which this handoff was written uses
  `/Users/nathan.cho/Documents/egg`.
- Unicorn uses `/home/nc437/egg`; raw runs are under
  `/home/nc437/egg/src/runs`.

Verify paths on each machine; do not assume they are interchangeable.

At handoff time, the local repo `/Users/nathan.cho/Documents/egg` was **not**
on current main. It was on:

```text
branch: agent/a6-closeout-package-integration
HEAD: d4adc341be4f69d38a4cdd777f95b902daa933a2
remote tracking branch: behind by 5 commits
```

That is still true at update time. The untracked contents have grown; the
local tree now also holds this handoff plus the task briefs written for the
Cursor round and the research note:

```text
.claude/
CURSOR_HANDOFF_B3_BASELINE_20260819.md
CURSOR_HANDOFF_PHASE012_20260814.md
LLM_HANDOFF_EGG_20260820.md            (this file)
CURSOR_HANDOFF_BNP_DICTATOR_20260820.md
CURSOR_HANDOFF_B1_MINIMAL_CYCLE_20260820.md
CURSOR_HANDOFF_UPLIFT_SETTLEMENT_20260820.md
CURSOR_HANDOFF_FROZEN_LOADER_20260820.md
CURSOR_HANDOFF_COLUMN_PROPOSER_20260820.md
CURSOR_HANDOFF_REPAIR_PR37_20260820.md
CURSOR_HANDOFF_REPAIR_PR38_20260820.md
CURSOR_HANDOFF_REPAIR_PR39_20260820.md
CURSOR_HANDOFF_REPAIR_PR42_20260820.md
CURSOR_HANDOFF_EXTEND_PR40_REGRET_20260820.md
CURSOR_HANDOFF_CI_20260820.md
CURSOR_HANDOFF_REVIEW_PR37_20260820.md
ref/review_notes/DEEP_RESEARCH_20260820.md
```

These handoff/brief files are deliberately untracked; they are operator task
prompts, not repository documentation. (PR #40 is separately being asked to
remove a task brief that was committed to its branch by mistake.) Do not run
`git clean`, `git reset --hard`, or blindly switch/pull and overwrite work.
Preserve or commit the local tree on a dedicated branch, then obtain a clean
checkout of current `origin/main` separately.

One concrete collision to expect: `ref/review_notes/DEEP_RESEARCH_20260820.md`
exists here untracked **and** is committed on branch
`research/deep-research-20260820` (draft PR #44). After that PR merges, delete
the local untracked copy before pulling, or Git will refuse the checkout.

The commits pushed from this machine used a temporary `git worktree` off
`origin/main` under the session scratchpad rather than switching this branch.
That pattern is recommended: it leaves the A6 working tree untouched.

On Unicorn:

- source `cluster/unicorn_env.sh` for the `/home/nc437/evsp_env` environment;
- expose Slurm tools with
  `export PATH="/usr/local/slurm/current/bin:$PATH"` in interactive shells;
- Gurobi evidence must fail rather than silently fall back to CBC;
- do not SSH from a Unicorn login node back into itself; the nested
  noninteractive shell previously lacked `squeue`;
- never print or commit license secrets.

## 12. GitHub/PR snapshot

Live-verified at update time. `main` = `ed8b06f3d7e8e4a7ecc5fbfd74ff0b819ac24fa4`.

Merged: PR #43 (CBC-only GitHub Actions CI — the newest and, for process
purposes, the most important), #36 (B3 factor pilot launcher/audit/analyzer),
#35 (EI-027 physical-bridge gate, second-stage A6 recovery), #34 (B3 factor
levels/screen freeze), #33 (EI-026 recovery path), #28 (A6 closeout
engineering); #30/#31 content is present on main.

Nine open draft PRs. **None has been merged; none is scored evidence.**

| PR | Head | What it is | State |
| --- | --- | --- | --- |
| #37 | `8144483` | B3 pilot closeout: analyzer, selection freeze, pack/import | Two independent reviews, 17 findings, all repaired. **Needs a third independent review.** Gates the flagship decision. |
| #38 | `1ae553f` | Tiny branch-and-price exactness laboratory | Hardened: `gurobipy` dependency reverted with a regression test that keeps it out; Gurobi suites skip cleanly on CBC; tolerance ledger; seed 11 at n=4 confirmed infeasible across all formulations. Root intervals matched A2's certified intervals exactly on seeds 0 and 15 — early evidence the B&P root really computes `z_CH`. |
| #39 | `2ad05f5` | Strict undamped two-cycle witness + minimizer | Repaired: backend-degeneracy replay fixed, tampering regressions, standalone CBC replay, base-load term corrected to `ops + (a + diag(b)U)·L + ½Lᵀdiag(b)L`. Merged main, so **CI passes — the first machine-verified PR.** |
| #40 | `71468ed` | Outcome-blind certified uplift settlement arithmetic | Reviewed and follow-up applied. A regret-accounting extension plus removal of a committed task-brief file was requested and is not yet done. |
| #41 | `3745c43` | Manifest-verified GIRO subset freeze/load | Cleanest of the round; touches only `load_frozen_subset` in existing code. Strong merge candidate. |
| #42 | `7b8fce1` | Local-move column proposer laboratory | Protocol violations forward-reverted (`e3a05be`, `7b8fce1`): no `result/` artifacts, no decision-log or status edits. Honest negative result: 0 of 160 proposals accepted under exact reduced-cost + replay admission. |
| #44 | `bf1099b` | `ref/review_notes/DEEP_RESEARCH_20260820.md` | Research notes only, no code. |
| #32 | `8d498b8` | B31 switch-boundary corpus builder | Cleanly merged with current main (no conflicts); 748 tests; no corpus generated. Later/optional. |
| #29 | `c32056a` | Cursor cloud-agent environment | Low scientific priority. |

Process rules that this round established, and that must survive:

1. **CI exists now.** Any PR branch that merges current main gets a
   machine-verified test count. Branches #37, #38, #40, #41, #42 predate the
   CI merge and therefore show no checks; merge main into each before trusting
   any number attached to it. Never accept a self-reported test count again.
2. **Author repairs, non-author reviews.** Every real defect this round was
   found by an agent that did not write the code. Never let a PR's author be
   its reviewer — the #37 review was deliberately given to an agent whose own
   work (the GIRO loader) was disjoint from B3.
3. **The Cursor identity gate cannot use `gh api user`.** Cursor agents
   authenticate as `cursor[bot]`, a GitHub App integration token, and GitHub
   forbids such tokens from calling `/user`: the call always returns HTTP 403
   "Resource not accessible by integration". This is **not** an authorization
   problem — those tokens push to `ndandnd/egg` fine. An agent asking for an
   `ndandnd`-authenticated `GH_TOKEN` does not need one, because commit
   authorship comes from `git config`, not from the push credential. The
   working gate is:

   ```bash
   git remote get-url origin | grep -q "ndandnd/egg"
   git config --local user.name "Nathan Cho"
   git config --local user.email "63525258+ndandnd@users.noreply.github.com"
   git push --dry-run origin HEAD
   ```

   Earlier commits in this repository carry `Cursor Agent` as primary author
   with `ndandnd` as co-author. Do not rewrite history to fix attribution;
   require correct authorship going forward via the `git config` lines above.

## 13. Recommended reading order for a new LLM

1. This file.
2. `README.md` and `HANDOFF.md` for original framing (not current status).
3. `doc/DECISION_LOG.md` for ratified decisions.
4. `doc/MEASUREMENT_RESULTS.md` for Phase 0/1/2 evidence.
5. `result/b2_full/20260818T140356Z/SUMMARY.md`.
6. `doc/B3_UPLIFT_BASELINE_SPEC.md` and
   `result/b3_baseline/20260820T025758Z/SUMMARY.md`.
7. `doc/B3_FACTOR_PILOT_SPEC_DRAFT.md` and the B3 screen manifest.
8. `src/experiments/b3_factor_pilot.py`, the driver, audit, analyzer, and
   launcher before touching the live B3 run.
9. `doc/A6_SPARSE_STABILIZATION_SPEC.md`, `doc/ENGINEERING_INCIDENTS.md`, and
   `doc/UNICORN_RUNBOOK.md` before touching A6.
10. `ref/RESEARCH_DIRECTIONS.md`, `ref/NOVELTY_MATRIX.md`, and
    `ref/READING_QUEUE.md` before writing novelty claims.
11. `ref/review_notes/DEEP_RESEARCH_20260820.md` before planning any ML
    work, market-realism work, or paper introduction — it carries the current
    novelty verdicts, the new citation candidates, verified data-access
    details, and the ML design contract.

`doc/RESEARCH_STATUS.md` is useful but was last updated before the latest A6
recovery and B3 factor-pilot work; it is not sufficient by itself.

## 14. Nonnegotiable continuation rules

1. Inspect primary repo/run evidence before inheriting a chat summary.
2. Preserve raw runs, claims, manifests, and incident artifacts.
3. Never score an incomplete or validity-failed population.
4. Never substitute seeds or change a frozen grid after seeing outcomes.
5. Keep synthetic evidence separate from theorem claims and external validity.
6. Keep A6, B3, and B31 evidence streams separate.
7. Do not merge a Cursor PR solely on its self-reported test count.
8. Use one guarded, subshell-wrapped Unicorn block; do not disconnect the user.
9. Prefer the smallest experiment that resolves the next preregistered gate.
10. Update the decision log, research status, and incident ledger when a gate
    genuinely closes.

## 15. One-paragraph state summary

The project has established, on a certified synthetic laboratory, that naive
price-taking tatonnement commonly cycles under moderate/strong fleet price
impact, that constant damping usually converts two-cycles into longer orbits
rather than reliable convergence, that strategic price-making nearly recovers
planner welfare, and that economically meaningful response discontinuities
are often duty changes. Plain certified column generation (A2) solves the
convex-hull coordination problem reliably; dense stabilized variants reduce
clean calls but lose on total calls, motivating the still-unscored A6 sparse
holdout. Separately, the B3 baseline certifies positive internal uplift on
38/64 synthetic instances. The preregistered 60-cell factor pilot was 59/60
certified at its last direct observation and its Slurm array has since left
the queue, so the immediate job is to verify the population properly (not
infer it from an empty queue), audit it, and freeze the decision — using the
hardened analyzer from PR #37 once a third independent review clears it. Close
the A6 recovery separately, then either run the prespecified fresh-seed B3
confirmation if GO or stop and reframe if not. A one-day Cursor engineering
round added nine unmerged draft PRs, including this repository's first CI, a
certified branch-and-price laboratory whose root reproduces `z_CH` exactly on
two burned seeds, and a machine-checked strict two-cycle witness for B1. A
six-agent literature sweep re-verified that the thesis combination is still
unoccupied and identified the demand-side convex-hull-pricing niche as open.
In parallel, turn the computational evidence into theorem targets, calibrate
the synthetic market against real published bid curves, and build the ML
warm-start harness outcome-blind while the cluster gates stay closed.


## 16. Research sweep of 2026-08-20 (late) and the ML direction

Six web-research agents (~110 searches, including a verified data-access pass
and a full-paper extraction pass) ran against the 2026-08-14 audited baseline.
Everything here is abstract-level confidence unless the note says a paper was
read in full; verify before citing in a manuscript. Detail and citation keys
live in `ref/review_notes/DEEP_RESEARCH_20260820.md`.

### 16.1 Novelty status

The claim still stands: no published work jointly occupies exact trip-covering
duties (Duties=Y) x endogenous shared price formation (EndogP=Y) x
certificate-bearing methods (Exact=C-a). Confirmed independently from the
exact-EVSP side, the power-markets side, and a direct threat hunt. The
literature continues to bifurcate — exact scheduling stays price-taking (at
most convex own-load cost proxies such as demand charges or peak terms), and
endogenous price formation stays convex, continuous, equilibrium-theoretic, or
heuristic on the fleet side.

Second, more actionable finding: **convex-hull pricing and uplift for an
indivisible demand-side asset has no occupant.** The 2025-2026 pricing
frontier (semidefinite-relaxation pricing, the European paradoxical-order
strong-duality line) is explicitly supply-side, and treats demand-side blocks
only through sufficient conditions. Our certified internal uplift for a
scheduled fleet is an opportunity rather than a threat — but two research
vectors could close it, so it should be claimed sooner rather than later.

Introduction differentiation set (the works a referee will ask about):
`yao2025` (nearest neighbor on the endogenous fixed point, and a coauthor's
work — write the positioning with Scaglione, not against her); Wu et al. 2021
TRB plus its newest descendant (exact duties with own-load cost proxies); and
Najafi & Fripp / Andrianesis et al. (certificate-bearing Dantzig-Wolfe price
coordination, but convex or generation-side). Add one sentence on the May 2026
Transportation Research Part C ride-hailing V2G bilevel as the freshest
fleet-side endogenous-pricing work.

Our own dictator preprint (arXiv:2508.06752) shows zero citations on OpenAlex.
Nobody has built on it; the formulation is public, so Chapter I has real but
not urgent timing pressure.

### 16.2 Scope correction the project owes itself

State the B2 result as: *dense iterative* stabilization loses end-to-end *at
small n*. Two facts forbid the broader claim. Stabilization gains are known to
concentrate on large, degenerate instances, so our `n in {8,12}` finding is
consistent with the literature rather than contradicting it. And the
dual-optimal-inequality family — including learned pairwise DOIs with an exact
recovery step — reports 55-83% total root column-generation time reductions at
*zero* bound loss, which is a stabilization win of a different kind.

Also: learned/adaptive stabilization control is now published prior art
(Wang & Khir, arXiv:2604.23889, with convergence guarantees, on cutting
stock). The A6 sparse event-triggered line must cite and position against it.

### 16.3 Market realism: the calibration path is now de-risked

The affine market `p_t = a_t + b_t (U_t + L_t)` is currently an assumption. It
can become a calibration cheaply, and a verification pass (including an actual
test download) settled how:

- **OMIE (MIBEL, Spain/Portugal) is the lead candidate.** Free, no
  registration, script-friendly: daily aggregated supply/demand curve files
  `curva_pbc_YYYYMMDD.1` (~4 MB/day, 2023 to present) and yearly ZIPs verified
  present for 2018-2022. Semicolon-delimited Latin-1, decimal comma, two
  header lines; `Tipo Oferta` C = demand / V = supply; both offered and matched
  steps.
  **Three corrections to the first version of this guidance, from a
  verification pass on PR #44 — the earlier text was too confident:**
  (i) OMIE's Legal Warning is *not* an explicit open-data license, so do not
  assert that fitted slopes are freely publishable; cite OMIE, identify the
  delivery channel and any transformations, and confirm the applicable
  attribution and reuse terms before submission.
  (ii) 15-minute trading intervals are *already live*, so a normal market day
  now has 96 periods, not "after late 2025" as originally written.
  (iii) A local slope fitted this way is neither an OMIE-published value nor
  the derivative of the full clearing model — EUPHEMIA handles block orders and
  complex conditions that a simple step-curve fit ignores. Treat the OMIE
  calibration as **exploratory** and do not call it validated until that gap is
  addressed explicitly.
- **Built-in validation:** the reconstructed supply/demand intersection must
  reproduce OMIE's published marginal price within one step. That catches
  parsing errors before they become results.
- **Watch:** DST days (23/25 periods) and the shift to 96 quarter-hourly
  periods after the SDAC 15-minute go-live in late 2025.
- Alternatives: Nord Pool aggregated bidding curves are paid (~EUR 430-1650
  per year per cluster, academic terms negotiable); EPEX is paid (EUR 200 per
  area per year, internal-use license); ENTSO-E publishes **no** day-ahead bid
  curves (prices and load only); the US fallback is ERCOT's free 60-day DAM
  disclosure, from which aggregate curves must be reconstructed per resource.
- Recipe per hour: parse to cumulative step functions, form the residual
  supply curve the fleet faces, then fit `b_t` in a +/- 250-1000 MW window
  around the clearing volume sized to fleet load, storing slope, window width,
  step count, and fit quality.

New empirical motivation citations worth adding to the introduction: a 2025
Nature Communications study on 760k+ real ultra-fast charging sessions
(synchronized rushes at off-peak onset; 2,000 stations raise the daily
peak-to-valley ratio by 31.6%; storage *worsens* surges at price transitions),
and a 2025 Norwegian study (~28k sessions) where fleet peak demand grows from
+31% to +54% as price sensitivity rises. These are exactly the
"self-defeating cheap charging" evidence the project has been asserting
qualitatively.

### 16.4 The ML direction (advisor's request), with a design contract

The advisor asked for machine learning to "learn the routes." The literature's
consensus architecture is **ML proposes, the exact oracle verifies and
certifies** — direct neural construction of feasible schedules under hard
coverage and state-of-charge constraints is not viable at certificate quality
(end-to-end learned pricing reports ~9% gaps). Our own measurements agree
independently: the local-move proposer went 0-for-160 under exact
reduced-cost-plus-replay admission (PR #42), and raw schedule identities carry
a measured 2,559-to-92 degeneracy-to-economics noise ratio. Successful methods
learn from **solver-internal signals** (duals, reduced costs, arc membership),
never surface structure.

Ranked targets for this project:

1. **Dual-trajectory warm starts across the price loop.** Learn (instance
   features, price-impact level, previous iterate's duals) -> converged
   restricted-master duals, used only to seed the negotiation. The closest
   published work is our setting almost exactly — fixed structure with a
   shifting parameter vector, where their demand profile plays the role of our
   price vector — reporting ~1.7-2.1x speedup to a *certified* gap, with
   public code. Lowest risk: the worst case is a bad stabilization center,
   never a wrong certificate.
2. **Learned pricing-network reduction.** Score arcs in the SOC-expanded
   pricing graph; cheap reduced pricing proposes and full exact pricing fires
   whenever the reduced version finds nothing. This has been done on
   multi-depot *electric bus* scheduling (3.5x average speedup at 2.2% cost
   loss) — read that paper first. As published it is heuristic-only, so
   certification requires adding an activity-check-and-release recovery step.
3. **Parametric strategy/support prediction.** Our loop re-solves the same
   instance at shifting prices, which is textbook parametric reoptimization;
   the security-constrained unit commitment precedent reports 4.3x faster
   *with optimality guarantees intact*.
4. **Pricing-value regression** to skip provably useless pricing calls; values
   are degeneracy-immune labels.
5. Column selection/retention in the master (only if the master, not pricing,
   dominates runtime).
6. Input-convex value-function surrogate giving a provable one-sided
   under-approximation of the negotiation value in the price (highest novelty,
   highest risk).

Non-negotiable design details, distilled from full reads of six papers:

- **Integration:** the prediction enters *only* as a frozen du Merle box
  center, with a penalty schedule that provably reaches zero (halve on clean
  mispricing, or the published `eps = c*/(c*-1)` rule when the minimum reduced
  cost `c*` is negative, else zero). Never inject predictions as raw duals,
  bounds, or certificates.
- **Labels:** scale-normalized, and either averaged across multiple optima or
  sampled from the optimal face. Last-iterate simplex duals are the noisiest
  possible label choice — this is the same degeneracy trap our own boundary
  measurements exposed.
- **Features:** prefer per-constraint featurization; whole-instance
  fixed-dimension nets break outside their trained sizes.
- **Do not** expect graph networks to transfer across changed underlying
  networks; two independent papers report failure, one catastrophically.
- **Report iterations and wall-clock separately.** Stabilized duals densify
  and slow pricing, routinely halving iteration savings when measured in time.

Data-generation architecture (outline now, cluster later):

1. **Generate (cluster).** Batch-solve 5-20k synthetic instances over
   n = 8-40 trips, stratified by seed x price-impact level x physics, using
   the existing certified drivers. Emit per-solve JSONL in the repository's
   provenance discipline: instance/market hashes, price vector, canonicalized
   duals, accepted columns with reduced costs and margins, certificates. This
   is one preregistered campaign, engineering tier, not a scientific result.
2. **Distill (deterministic, hashed).** A dataset builder applying the two
   degeneracy defenses: canonical dual labels, and margin filtering that drops
   examples where alternatives are not economically separated — reusing the
   existing boundary machinery's economic filter.
3. **Train (single GPU, hours).** Gradient-boosted baselines first, graph
   networks second.
4. **Integrate behind the certificate.** Predictions only seed warm starts or
   propose columns; A2's clean-call accounting measures the win.
5. **Evaluate per axis.** Hold out the largest sizes and unseen price-impact
   levels and report both.

**Preregister this kill criterion before building anything:** the mandatory
cheap baseline is *reuse the previous loop iterate's duals* (or k-nearest
neighbors over previously solved price points). It costs nothing. An ML method
that cannot beat it is dead, and saying so plainly is a result.

Stages 2-4 are pure code plus adversarial tests, buildable now, outcome-blind.
Stage 1 needs the cluster and must wait behind the B3 decision freeze.

### 16.5 Venue fit

The universal bar is **speedup at unchanged certificate quality**, reported
with-guarantees and without-guarantees separately. INFORMS Journal on
Computing is the best fit for an "ML-warm-started certified negotiation"
paper (its direct precedents live there, and it mandates comparison against
state-of-the-art exact baselines plus code/data reproducibility);
Transportation Science fits if the EVSP-plus-price-feedback application
carries the paper; EJOR is the more forgiving methodological home; IEEE TPWRS
or Energy Economics for the price-formation and uplift half, expecting the
calibrated market of section 16.3. A machine-learning venue is only plausible
for a generic contribution — the candidate there is our degeneracy-robust
labeling methodology, since few papers actually *measure* multiple-optima
label noise and we have the 2,559-versus-92 measurement.

"We added a graph network to column generation for problem X" is incremental.
A new lever — dual warm-starting a *certified* negotiation under parametric
price shift, with a guarantee-preserving architecture and honest
equal-certificate accounting — is not.

### 16.6 What the sweep says not to do

Do not claim "first price-making EV fleet" or "first EVSP whose cost depends
on its own load" (demand-charge and peak-load MILPs are the prior art for the
degenerate convex case). Do not claim stabilization fails in general. Do not
treat `yao2025` as a competitor. Do not build a second settlement evidence
contract when PR #40 already defines one. Do not launch the ML data campaign,
the paused 576-cell A1 grid, the old 960-cell campaign, or a fresh-seed B3
confirmation to fill idle cluster capacity.

## 17. Operator window plan (2026-08-20 evening, before an extended break)

Operator constraint recorded at update time: the last interactive cluster
session is roughly 12 hours away, after which the operator is unavailable for
an extended period and will check results on return. The planning goal is
therefore that the **final session launches something that completes during
the break**, rather than spending that session discovering state.

The critical path to a launchable experiment is the B3 decision, and it has
five steps that must happen in order. Only the first two need the operator and
the cluster; they take minutes, not hours. Do them EARLY in the window, not at
the end:

1. **Verify the population** (operator, cluster, ~15 min). `sacct` on the
   array plus the hardened audit; see section 9.1/9.2. This is the step that
   converts "the queue is empty" into "the population is complete".
2. **Audit** (operator, cluster, minutes; deterministic, no solver).
3. **Third independent review of PR #37** (agent, hours) — runs in parallel
   with nothing blocking it, and must finish before the analyzer is trusted.
4. **Analysis** (operator, minutes, no solver) from the reviewed analyzer
   commit.
5. **Freeze the selection artifact and commit the decision.**

If steps 1-2 happen early and 3 runs in parallel, the decision can be frozen
inside the window and the final session has something preregistered to launch.

### What may be launched in the final session

- **If the decision is a committed GO:** the prespecified fresh-seed B3
  confirmation (seeds 32-37, S0 versus the selected factor only, 24 matched
  contrasts = 48 method-cells, gate >= 18/24 direction-consistent
  zero-excluding and signed median > 0.04). Sizing precedent: the 60-cell
  pilot at the same epsilon/budget on comparable instances completed well
  inside a day at concurrency 12, so 48 cells should land inside the break
  window comfortably.
  **The confirmation driver does not exist yet.** Building it is the single
  highest-value agent task in this window. Build it outcome-blind and
  parameterized on the selected factor, and give it a structural guard: it
  must refuse to run unless fed a committed GO selection artifact whose
  hashes and provenance validate. That preserves the intent of the
  "only a committed GO authorizes confirmation implementation/launch" rule
  while allowing the work to proceed in parallel; note the deviation from the
  letter of that rule explicitly in the PR.
- **If the decision is NO-GO or UNDER-RESOLVED:** launch no confirmation. That
  is the preregistered outcome, not a failure, and inventing a
  tolerance-tightening or seed-extension experiment on the spot would violate
  the frozen design.
- **If the audit fails:** launch nothing scientific. Preserve raw evidence,
  classify the engineering incident.

### The break-safe engineering-tier job

Independent of the B3 outcome, the **ML data-generation campaign** (section
16.4 stage 1) is a good break job: embarrassingly parallel, engineering tier
rather than scientific evidence, and useful for every candidate ML target
because duals, arc membership, and pricing values all come out of the same
solve logs.

Three conditions on it:

1. **Disjoint seed namespace.** Every existing seed range is committed to
   something: 0-15 burned by the B2/B3 population, 16-31 the A6 holdout,
   32-37 the B3 confirmation, 38-47 reserved. Generate ML training data from a
   clearly separated high range (for example 10000+) so it can never
   contaminate a scientific population.
2. **A bounded first tranche, sized to land.** Do not launch an open-ended
   5-20k-instance campaign blind into a cluster that already has ~70 unrelated
   jobs on it. Launch a tranche (order 1-2k instances, n = 8-16) with an
   explicit wall-clock cap chosen to finish inside the break. A tranche that
   completes is worth more than a campaign that gets killed.
3. **The emission format is the deliverable**, not the count: per-solve JSONL
   carrying instance/market hashes, the price vector, canonicalized duals,
   accepted columns with reduced costs and margins, and certificates. Get that
   schema reviewed before launch, because a campaign with the wrong logging is
   a campaign that must be re-run.

### Also do inside the window (no compute needed)

- **The A6 holdout recovery closeout.** The raw run from job `248911` already
  exists on Unicorn; only packaging and validation stand between it and a
  scoreable A6 adoption-gate result. This costs no cluster time and closes a
  whole line. Do it early in the window with attention rather than in the last
  minutes: the second-stage recovery path is one-shot.
- **Merge current main into PRs #37, #38, #40, #41, #42** so CI reports on
  them, and merge PR #41 if its CI is green.

### 17.1 Population VERIFIED — audit PASS (2026-08-20 evening)

Steps 1 and 2 of the window plan are done. Recorded here because this is the
gate the whole program was waiting on.

`sacct -j 311153` shows all 60 array tasks `COMPLETED` with exit code `0:0`.
Elapsed times ranged from 5 seconds to `01:43:47`; total across the array was
about 5.1 CPU-hours.

`experiments/audit_b3_factor_pilot.py` on `runs/b3_factor_pilot` returned:

```text
frozen screen: result/b3_factor_screen/20260820T105318Z
screen record sha256: 27c04d82bc88b62eed84394569b3ab8a35238a3a57c9cf4ba6463fb85f7bf603
run manifest sha256: 9f7529fce6ce0915ed1bfe30887ea64840d8060d871d5c60283bd3ed61a529b6
run commit: 5b63e725d0fd85cfb0b83f462a612016e7f4321a
certified A2 cells: 60/60
converged dictators: 60/60
per-setting cells: S0 12, S1 12, S2 12, S3 12, S4 12
result: PASS
```

Backend was Gurobi (`[egglab] backend=GRB`), as required for cluster evidence.

**The preregistered analysis has deliberately NOT been run.** Holding it keeps
the third independent review of PR #37 genuinely outcome-blind, and there is
no operational cost to waiting: see the timing finding below.

### 17.2 Timing finding: the confirmation does not need an overnight window

The pilot's own accounting settles the scheduling question. Sixty cells cost
about 5.1 CPU-hours in total, the longest single cell took 1h44m, and at
concurrency 12 the array's wall clock was therefore roughly two hours. The
confirmation population is 48 method-cells of comparable size, so it should
also complete in about two to three hours.

Consequences:

- There is no reason to rush the analysis or the decision freeze to catch an
  overnight window. The confirmation fits inside an ordinary working session.
- Nothing else is both authorized and coded: the confirmation driver does not
  exist yet, the ML data driver does not exist yet, the A6 closeout is a
  minutes-long packaging operation that deserves attention rather than a
  pre-sleep launch, and the paused A1/960-cell campaigns remain forbidden.
- Therefore the correct overnight work is **agent work, not cluster work.**
  Three briefs were written for it:
  `CURSOR_HANDOFF_REVIEW3_PR37_20260820.md` (third independent review of the
  repaired closeout; explicitly outcome-blind),
  `CURSOR_HANDOFF_CONFIRM_DRIVER_20260820.md` (confirmation driver,
  parameterized on the selected factor, structurally gated on a validated
  committed GO artifact), and
  `CURSOR_HANDOFF_ML_DATA_DRIVER_20260820.md` (training-data emission driver,
  seeds >= 10000 only, canonicalized duals, margins, per-cell wall-clock cap).

### 17.3 Order of operations for the next session

1. Collect the third #37 review. If it clears, merge main into #37 for CI,
   then merge #37.
2. Run the preregistered analysis from that reviewed analyzer commit, review
   the tables, regenerate byte-for-byte, and commit the artifact under the
   code-first/artifact-second protocol.
3. Freeze the machine-readable selection; update `doc/DECISION_LOG.md` and
   `doc/RESEARCH_STATUS.md`.
4. If and only if the frozen decision is GO, launch the confirmation with the
   reviewed driver (~2-3 hours; it will finish well inside the session).
5. Close the A6 holdout recovery with attention — it is one-shot, and its raw
   run from job `248911` already exists, so it converts existing compute into
   a scoreable adoption-gate result at zero cluster cost.
6. Optionally launch a bounded ML data tranche once its schema has been
   reviewed.

### 17.4 Third review of PR #37: verdict and what it changes

The third independent review (outcome-blind, synthetic probes only, built in a
throwaway detached worktree) returned **conditionally safe**. Its substance:

**Confirmed correct.** The frozen §6 rule is implemented exactly, in both the
analyzer and the selector's independent recomputation: interval contrasts on
**raw** endpoints, direction-signed zero exclusion, median of signed
midpoints, tie-break by count then signed median then fixed factor order, and
the `<= 0.04` / `> 0.04` / `>= 9` comparisons as frozen. Synthetic probes
confirmed count 9 gives GO and count 8 gives NO-GO. All four of the repair
author's recorded disagreements were independently judged justified: `os.link`
is the right no-replace primitive and has no link-then-verify gap (same
directory, so `EXDEV` cannot occur); the marker-plus-completion-record
protocol has no crash window an import can misread; the transactional single
reads genuinely parse the hashed bytes; and INVALID/HALT analyses are
correctly unpackable.

**Two of three prior blockers could not be re-exploited.** A decision-only
edit with every hash recomputed was refused because the selector recomputes
from primitives. An internally consistent `raw_binding` describing a different
job was refused by the packager's cross-binding check.

**One new MAJOR, closable.** The selector authorizes a *fabricated* analysis
directory: provenance rests only on a self-described boolean, two public
frozen constants, and any real ancestor commit, and the selector ignores
`raw_binding` entirely, so it never re-binds to `runs/`. The reviewer emitted a
GO analysis directory with no run behind it and the selector wrote
`SELECTION.json`. Repair brief: `CURSOR_HANDOFF_REPAIR2_PR37_20260820.md`.

**One residual MAJOR, disclosed rather than closable.** The analyzer proves
the recorded event logs are internally consistent and reproduce the stored
summary; it cannot prove they came from real solves. The reviewer raised a
cell's `lb_best` from 98.5 to 100.0 by co-editing `z_rmp_model`,
`duals_sigma`, `min_reduced_cost_lb`, `lb_ch`, `lb_best`, and the histories
consistently while leaving the pricing oracle's `solver.bound` untouched, and
the replay accepted it. Because `U_hi = z_D_ub - lb_best`, that moves every
contrast and the decision.

The honest reading: **the certificate attests replay, not re-solve.** Decision
integrity therefore rests on the provenance of `runs/b3_factor_pilot`. There is
no adversary in this project, but agents do have write access to run
directories and one has already written unreviewed artifacts into `result/`,
so the exposure is accidental corruption and well-meaning agent edits, not
malice. Two cheap mitigations follow, and both are recorded in the repair
brief: an independent pre-analysis raw-tree digest (below), and an optional
`--verify-rmp` mode that re-solves each final restricted master as an **LP over
the stored, replay-validated column pool** — closing most of the co-edit
surface at LP cost with no MIP re-solve.

**A float knife-edge worth stating.** A true median of exactly `0.04` is not
IEEE-754-representable, so a result infinitesimally near the threshold can
resolve either way depending on accumulation order. The rule must not change.
The repair adds a pure disclosure — `boundary_margin`, `boundary_adjacent`,
and the median at full precision — so a knife-edge is visible rather than
silently resolved. That addition is only legitimate because it is being made
before anyone has seen the outcome; it must not be made afterwards.

### 17.5 Do this BEFORE running the analysis: capture the pre-analysis anchor

This is the one action that cannot be recovered later. Right now the raw tree
is audited and nobody knows the outcome, which is the only moment when a digest
of it carries the claim "taken while still blind." Run on Unicorn:

```bash
(
    set -euo pipefail
    cd "$HOME/egg/src"
    python3 - <<'PY'
import json, sys
sys.path.insert(0, ".")
from experiments.package_a6_holdout import (
    snapshot_source, canonical_tree_sha256)
snap = snapshot_source("runs/b3_factor_pilot")
print(json.dumps({
    "tree_sha256": canonical_tree_sha256(snap),
    "file_count": snap["file_count"],
    "directory_count": snap["directory_count"],
    "total_bytes": snap["total_bytes"],
}, indent=2, sort_keys=True))
PY
)
```

`snapshot_source` and `canonical_tree_sha256` are on main already (they came in
with the A6 packaging work), so this needs no unmerged branch, and it uses the
**same algorithm** the packager and the repaired selector compare against.
Record the printed digest somewhere durable — commit it as a one-line
pre-analysis anchor note, or at minimum paste it into the decision log — and
have the repaired selector check the analysis `raw_binding` against it.

### 17.6 A replication run is the best available break job

An independent re-run of the same 60 cells into a **different output
directory** is the strongest cheap answer to the replay-not-re-solve
limitation, and it is a legitimate use of the break window:

- it costs about 5.1 CPU-hours, roughly two hours wall clock at concurrency 12,
  bounded below by the single 1h44m cell;
- it needs no new code — the merged pilot driver already accepts `--out`;
- it is verification tier, not a new scientific population: same seeds, same
  settings, same frozen screen. It creates no new evidence and touches no
  reserved seed range.

Two rules on it, which must be stated before it runs:

1. **The original run stays canonical.** The replication is a verification
   artifact only. If the two disagree beyond the declared tolerance, that is an
   engineering incident to investigate — never a choice of which run to score.
   Never use the replication to shop for a preferred outcome.
2. **Compare certified intervals within tolerance, not bytes.** A MIP solver
   need not reproduce identical logs across runs; the claim being tested is
   that the certified intervals agree, not that the files match.

If the replication reproduces the certificates, the residual forgery class
becomes empirically implausible and the thesis can say so. If it does not,
that is something the project needs to know before publishing, not after.

### 17.7 HAZARD: the pilot submit script hardcodes its output directory

`src/cluster/launch_b3_factor_pilot.sh` takes its run directory from
`EGG_RUN_OUT` (default `runs/b3_factor_pilot`) and uses it for the
fresh-directory guard and for atomic manifest emission. But
`src/cluster/submit_b3_factor_pilot.sub` ends with a hardcoded

```bash
python experiments/run_b3_factor_pilot.py --cell "${SLURM_ARRAY_TASK_ID}" \
    --out runs/b3_factor_pilot
```

so the array tasks ignore `EGG_RUN_OUT` entirely. Launching a replication with
`EGG_RUN_OUT=runs/b3_factor_pilot_replication` therefore passes every launcher
guard — the new directory is fresh, its manifest is emitted, the job binds and
releases — and then **60 array tasks write into the original audited tree.**
That would invalidate the pre-analysis anchor
`efc5ca31dcddb21166f6a5da2cf60b4961706c99edf9dbda882f87a18a88ace4` and destroy
the only clean provenance the flagship decision has.

Do not launch any replication or re-run of the pilot until the submit script
threads the output directory through (`--out "${EGG_RUN_OUT:-runs/b3_factor_pilot}"`,
exported by the launcher so the array inherits it), with a shell-level test
proving the array command targets the overridden path. Until then, treat
`launch_b3_factor_pilot.sh` as single-use: it can only ever be run again
safely against a directory the driver will not collide with.

Note also that the per-cell driver's resume logic means the collision might
not be loud: completed cells with matching identities may simply no-op or
rewrite byte-identical logs, so the tree could be silently touched rather than
visibly corrupted. Content-addressed digests would catch a real change, but
"probably idempotent" is not a guarantee worth betting the flagship on.

### 17.8 Fourth look at PR #37: CLEAN. PR #45: three criticals, do not launch

**PR #37 @ `0af91df` (CI-green, 802 tests) is verified and mergeable.** A
fourth independent verification pass confirmed both third-review MAJORs are
closed, and the mechanism is worth understanding because it changes what the
flagship certificate rests on.

The repair adds `src/experiments/b3_pilot_anchor.py` holding
`FROZEN_RAW_ANCHOR` — the operator's outcome-blind pre-analysis capture
(`tree_sha256 efc5ca31...ace4`, 363 files, 60 directories, 17385781 bytes) —
and both the analyzer and the selector now recompute the live tree's identity
and refuse any disagreement. Consequences:

- the fabricated-analysis-directory forgery is refused, because a fabricated
  directory's runs tree cannot match the frozen anchor without *being* the
  genuine audited tree;
- the un-closable "replay proves consistency, not real solving" residual is
  now **backstopped rather than open**: any self-consistent co-edit of a cell
  changes the tree bytes, so the canonical tree SHA no longer equals the
  anchor and the population becomes INVALID/HALT at both the analyzer and the
  selector. The residual is reduced from "forge a consistent record" to
  "forge a tree with the exact frozen SHA," which a co-edit cannot do.

Verified additionally: no rule, threshold, or comparison operator changed
(checked by executable equivalence across `{med, count}` combinations with
zero mismatches); `AUDIT.md` is the sole optional root file and any other root
file refuses *and* trips the anchor via `file_count`; `boundary_margin` and
`boundary_adjacent` are computed after the state and never read by it.

Two disclosed notes, neither a defect: the anchor's authority rests on the
operator's capture being correct (that is the documented trust root), and a
`verify_code_commit=False` test seam relaxes the anchor to the live tree —
production exposes no CLI path to it, but it must never become reachable from
a runnable entry point.

**PR #45 @ `da2cdb6` must not launch anything.** An independent review (by an
agent that did not write it) found three criticals and three highs, against
the author's self-report of a comprehensive gate:

1. **Critical** — fabricated, *uncommitted* selection artifacts pass as GO: the
   gate never proves the artifact bytes are tracked and committed at the
   declared `selection_code_commit`. An artifact with invented hashes,
   `count=999`, `direction_sign=true`, non-finite boundary values, and missing
   required fields was accepted.
2. **Critical** — launcher environment hooks bypass the gate entirely:
   production permits an `EGG_PILOT` override and `EGG_LAUNCH_SELFTEST`
   disables guards, so a substitute command can fake dry-run/manifest/list/bind
   success. Even `boundary_adjacent == true` is bypassable at launcher level
   despite the Python loader correctly refusing it.
3. **Critical** — an unbound array can become runnable: non-atomic
   exists-then-replace binding, a worker that never checks `JOB.json` against
   `SLURM_ARRAY_JOB_ID`, a directly submittable `.sub`, and the same
   hardcoded-output-path defect as §17.7 (`EGG_RUN_OUT` binds the launcher
   while the worker hardcodes `runs/b3_confirmation`).
4. **High** — the spec-mandated fresh-grid structural screen is absent, so
   seeds 32-37 could be spent before an invalid frozen design is detected.
5. **High** — incomplete field/type validation (missing `campaign` and
   `baseline_level` pass; `direction_sign=true` accepted as `+1`; counts above
   the possible 12 pass; `NaN`/`Infinity` pass).
6. **High** — the post-run audit makes selection validation optional.

Repair brief: `CURSOR_HANDOFF_REPAIR_PR45_20260821.md`. The PR needs another
independent review after repair before it may ever launch.

**The lesson to keep:** #45's author self-reported a comprehensive GO gate in
convincing detail, and an independent reviewer found three criticals in it.
Author self-reports describe intent, not coverage. This is the second time this
pattern has held in two days.

### 17.9 Revised plan: freeze the decision, launch nothing

Because #37 is clean and #45 is not, the two halves of the plan separate:

- **Do** merge current main into #37, merge #37, run the preregistered
  analysis, read `boundary_adjacent` first, then freeze the selection artifact
  and commit the decision. This is safe, takes minutes, and is the
  preregistration payoff. Freezing early also locks the outcome before anyone
  can be tempted by it.
- **Do not** launch the confirmation. Seeds 32-37 are one-shot and #45 can
  currently be made to launch on a forged authorization, or to spend the seeds
  before the mandatory design screen runs. The cost of waiting is calendar
  time only: the confirmation is a two-to-three hour job whenever it runs.
- **The replication remains blocked** until the §17.7 submit-script fix lands.

### 17.10 Operating habits adopted from the adjacent project's campaign

The operator's parallel project produced a cluster operating-rules document
(`CLUSTER_OPERATING_RULES_20260821.md`, decision D0033, in that project's
repository). Several of its habits transfer directly and are adopted here:

1. **Never assume a Cursor branch name.** `git ls-remote --heads origin`
   first; Cursor appends suffixes (`-eea3`, `-5fa0`, ...) and honored an exact
   requested name only once.
2. **Write a file then run it** (`cat > f <<'EOF'`), rather than long
   heredoc'd bash blocks with nested `--wrap "..."` strings, which get mangled.
3. **One paste block per request.**
4. **A socket timeout is a reply timeout, not a submission failure.** Verify by
   counting queued jobs, never by exit code — this nearly caused 21 duplicate
   submissions.
5. **Chain dependent work at submit time** with `--dependency=afterany`,
   guarded so a missing input writes a `.skipped` marker and exits 0.
6. **Never modify a checkout that running jobs read from — make a new one.**
   This one bites `egg` directly: array tasks execute from `$HOME/egg/src`, so
   merging PRs or pulling while an array is live would have later tasks run
   different code than earlier ones. The per-cell `run_commit` binding means
   the audit would *catch* it, but the run would be wasted. **Do not merge or
   pull on Unicorn while an egg array is running.**
7. **`--wrap` batches carry no provenance.** Snapshot `sacct -X -P` before
   walking away.
8. **`bash -x` on the real invocation** is the fastest diagnosis of a silent
   Slurm failure; `|| return 2` with `2>/dev/null` hides everything.

### 17.11 PR #47 reviewed and mergeable; two checks before any replication

PR #47 (`cursor/b3-submit-out-fix`, head `ef95127`, CI-green at 721 tests)
fixes the §17.7 hazard. The diff was reviewed line by line:

- `launch_b3_factor_pilot.sh`: a single change, adding
  `--export="ALL,EGG_RUN_OUT=${OUT}"` to the sbatch invocation. No other line
  touched, and the eight pre-existing guard tests pass unmodified.
- `submit_b3_factor_pilot.sub`: refuses a set-but-empty `EGG_RUN_OUT` using the
  correct idiom (`-n "${EGG_RUN_OUT+x}" && -z "${EGG_RUN_OUT}"`), resolves
  `OUT="${EGG_RUN_OUT:-runs/b3_factor_pilot}"` as a **relative** path that
  resolves after the script's own `cd`, keeps `export EGGLAB_REQUIRE_GRB=1`
  unconditional and ahead of the environment source, and invokes the driver
  with `--out "${OUT}"`.
- `test_b3_launcher.py`: four new tests — the export token on the recorded
  sbatch line, array targeting by executing the real `.sub` with a stub
  interpreter (recorded argv
  `experiments/run_b3_factor_pilot.py --cell 7 --out <override>`), the default
  preserved when unset, and empty refused with no driver invocation. All four
  were demonstrated to fail against the unfixed scripts by reverting the two
  cluster files.

**NOTE (not a blocker, but fix it or check for it).** `EGG_PYTHON` and
`EGG_ENV_SCRIPT` are now honored **in production**, not only under a test
flag. Because the launcher passes `--export=ALL,...`, a stray `EGG_PYTHON` in
the operator's login shell would silently propagate to all 60 array tasks and
change which interpreter runs the driver. The risk is far smaller than the bug
being fixed — it forges no authorization, and per-cell `run_commit` binding
plus the audit would surface anomalies — but it is the same *class* of defect
as PR #45's Critical 2, and the same standard should apply: honor those two
overrides only when `sbatch` is absent from `PATH` (i.e. off-cluster). Request
that as a follow-up.

**Two checks before launching any replication:**

1. Confirm no stray overrides are exported in the launching shell:

   ```bash
   env | grep -E '^EGG_(PYTHON|ENV_SCRIPT)=' && echo "UNSET THESE FIRST" || echo ok
   ```

2. Confirm the **solve path is unchanged** since the original run, so the
   replication tests reproducibility rather than conflating it with a code
   change. The original pilot ran at `run_commit = 5b63e72`; merging #37 and
   #47 moves HEAD, so verify the computation itself did not move:

   ```bash
   git diff --stat 5b63e725d0fd85cfb0b83f462a612016e7f4321a..HEAD -- \
       src/egglab/ \
       src/experiments/b3_factor_pilot.py \
       src/experiments/run_b3_factor_pilot.py
   ```

   This must be empty. (#37 touches the analyzer, packager, and selector;
   #47 touches the launcher and submit script; neither should touch the solve
   path.) If it is non-empty, stop and read the diff before launching — the
   replication's meaning depends on it.

Expect the replication's cells to be bound to the new merged commit rather
than `5b63e72`. That is correct and expected: the comparison being made is
*certified intervals agree within tolerance*, not that run manifests match.
The original run stays canonical either way.

### 17.12 Fifth-review adjudication (2026-08-21, late): board corrections

An independent review of the status board itself found two blockers and several
stale entries. Adjudication, with what was verified by hand:

**Accepted in full.**

1. **A replication needs a frozen comparator before it launches.** This is the
   strongest point in the review. "Certified intervals agree within tolerance"
   is prose. A comparator must be written and frozen first, naming: which
   cells, which fields (`lb_best`, `ub_ch`, both endpoints of the uplift
   interval), the tolerance and whether it is absolute or operand-scaled, what
   counts as agreement (60/60, or a stated allowance), and what a single
   disagreement triggers (incident, not a choice of which run to score). Same
   preregistration logic the rest of the program already follows.
2. **"Novelty re-verified" was too strong.** Correct wording: no collision
   found in this sweep; canonical ingestion, dimensional scoring, and full-text
   verification remain pending. Board corrected.
3. **#38, #41, #42 have no CI on their exact heads — verified.** The board's
   earlier "#41 is the cleanest merge candidate" contradicted this program's
   own rule and is retracted. #39, #45, #46, #47 are CI-green.
4. **Rerun the newly merged audit read-only, without `--out`.** The recorded
   PASS came from the pre-#37 audit implementation. Never pass `--out` into the
   raw tree again: `AUDIT.md` is already one of the 363 anchored files, so
   rewriting it can change the tree SHA and break the anchor.
5. **Park PR #46**, produce-don't-execute scope for the A6 preflight, PR #45
   brief verbatim with a different reviewer afterwards, keep `main` stable until
   the decision is frozen, and preserve the handoff and live briefs on a
   dedicated ops branch (never `git add -A`).

**Accepted with a scoping correction — the findings are real, the framing is
not quite right.**

6. **#37 shape-only `run_commit`.** Real gap, and it was in the *first* review's
   findings; it was lost when those were consolidated into the repair brief.
   Fix it. But verified by hand: `5b63e72` resolves to a real commit object and
   is an ancestor of `main`, so **this population's provenance is genuine**, and
   `MANIFEST.json` is one of the 363 anchored files, so tampering with the
   recorded commit changes the tree SHA and trips the anchor. The gap prevents a
   *future* forged manifest; it is not a live exposure for this decision.
7. **#37 scoring the live tree before freezing.** Real, and the proposed fix
   (freeze once with `freeze_source`, verify the frozen copy against the anchor,
   audit and score only that copy, re-verify the live source afterwards) is the
   right design. Its exploitation requires a process racing a roughly
   thirty-second local read, and nothing has write access to that tree: no egg
   array is running and no agent in this campaign has cluster access. Fix it,
   but do not read it as evidence that the population was scored wrong. The
   operational equivalent for the one run that matters is to compute the anchor
   digest immediately before and immediately after scoring and record both.
8. **#47.** The demonstrated rc=0/no-evidence bypass
   (`EGG_PYTHON=/usr/bin/true`, `EGG_ENV_SCRIPT=/dev/null`) is new and real, as
   is the comma-delimited `--export` grammar issue. But **worker
   non-authentication of `JOB.json` against `SLURM_ARRAY_JOB_ID`, and direct
   submittability of the `.sub`, are pre-existing properties of this pipeline
   that also applied to the canonical run.** They are worth fixing, and the
   scope should say so honestly: that is a hardening project for the array
   contract, not a regression introduced by #47.

**The judgment call, stated so it can be audited.** Freezing the decision now
with a manual double-anchor check would be defensible, and the arithmetic would
not change. It is nevertheless the wrong trade: the repairs are two-to-four hour
agent jobs, and committing an immutable decision artifact from code with two
open findings — immediately before the only person who could defend it becomes
unavailable for days — buys calendar time at the cost of a permanently
awkward provenance story. **Spend the window on repairs, not launches.**

There may be no authorized run in this window at all. If the gates are not all
green, launching nothing is the correct scientific outcome, not a failure.
