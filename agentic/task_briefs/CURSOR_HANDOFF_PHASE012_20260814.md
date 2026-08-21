# Cursor implementation handoff: Phase 0/1/2 price-feedback experiments

Date: 2026-08-14. Audience: a Cursor agent with zero prior context.
Owner: Nathan Cho. Repo: `/Users/nathan.cho/Documents/egg` (github.com/ndandnd/egg).

## 0. Context in five sentences

This is PhD-thesis research on the price-maker electric vehicle scheduling
problem (EVSP): a bus fleet's charging load is large enough to move the
electricity price that the schedule itself was optimized against
(price -> schedule -> load -> price). The naive iteration of that loop is,
formally, unstabilized Dantzig-Wolfe/Lagrangian decomposition of an
integrated planner ("dictator") problem; cycling and damping behavior tied
to the integrality gap is the scientific object, not a nuisance. Your job is
NOT to prove any of that. Your job is to build the experimental substrate:
a logging contract (Phase 0), a synthetic price-response outer loop over an
existing exact EVSP solver (Phase 1), and a switch-boundary mapping study
(Phase 2). Everything you build must carry honest exactness labels — this
project has previously withdrawn overclaimed results and treats labeling as
a hard constraint.

## 1. Repositories and the oracle rule

- **This repo (`egg`)**: all new code goes here. Before starting, merge or
  check out `origin/cursor/deep-lit-research-5fa0`, which contains the repo
  structure (`src/` code, `result/` outputs, `doc/` write-ups, `ref/`
  literature). Read `HANDOFF.md` and `ref/context/HANDOFF_PRICE_MAKER_20260814.md`
  Section 7-8 on that branch first.
- **EVSP-DR** (`/Users/nathan.cho/Documents/demandResponse/EVSP-DR`, branch
  `peel-and-price`, commit `b50d648` at handoff time — verify and pin): the
  exact price-taking EVSP machinery on Swedish (Partille) bus data.
  **Hard rule: never modify or copy code from EVSP-DR.** Wrap it (import or
  subprocess) as an oracle. Record its commit hash in every run record; abort
  if the checkout differs from the pinned hash.
- Relevant EVSP-DR entry points (verify signatures by inspection before use):
  - `src/rerealize_routes.py` — fix a trip sequence, re-optimize its charging
    under a new tariff, replay-validate. This is the cheap inner oracle.
  - `src/master.py` / `src/master_lp_scipy.py` — restricted master (MIP / LP
    with duals) over duty columns.
  - `src/exact_pricer_expanded.py` — SOC-by-time expanded exact pricer;
    produces an LP pricing certificate on the discretized route space. Slow;
    use only where specified.
  - `src/run_exact_pool_mip.py` — integer schedule from a column pool
    (finite-pool optimum only, never "optimal schedule").
  - `src/analyze_peak_shift.py` — hourly load aggregation (re-validate its
    output against the schedule before trusting it).
- Instances: small Partille cases `k=8` and `k=13`. Do not use larger cases.

### 1.1 Known trap (do not skip)

Stored duty columns are tariff-specific in their charging realization and
cost. Applying a new price vector to old charging events is only "exposure of
a fixed realization," not a response. The exact pricer also deduplicates
candidate columns by trip set (`frozenset(trips)`), which can discard distinct
charging realizations of the same trip sequence. Therefore: at every new
price vector, every reused trip sequence must be re-realized via
`rerealize_routes.py` before its cost is reported.

## 2. Task 0 — Oracle interface + logging contract (Phase 0)

1. Write `doc/ORACLE_API.md`: the actual call signatures, inputs, outputs,
   and units of the four EVSP-DR entry points above, discovered by reading
   the code. Flag any ambiguity (e.g., price units, station mapping,
   terminal-SOC policy) as an open question rather than guessing.
2. Implement `src/runlog.py`: a JSONL run-record writer + schema validator.
   One record per oracle solve / outer iteration with at least:
   - instance id, input hash, `egg` commit, EVSP-DR commit, random seed;
   - full price vector and the price-map parameters (a_t, b_t, alpha, ...);
   - selected trip sequences + a stable schedule hash (hash of the sorted
     canonical trip-sequence tuple, NOT of floating-point costs);
   - charging realization: station-hour kWh, aggregate hourly load L_t,
     fleet size, deadhead km, charge events, initial/terminal SOC;
   - objective decomposed: bus fixed cost, deadhead, electricity, other;
   - **oracle tier** (enum, required): `fixed-realization` |
     `re-realized` | `restricted-pool` | `capped-dp` | `exact-expanded`;
   - solver status, LP reduced-cost bound if available, integer pool gap,
     wall time, artifact paths.
3. Acceptance tests (AT-0):
   - schema validator rejects a record missing `oracle_tier` or either
     commit hash;
   - a round-trip (write, read, validate) test passes;
   - two solves of the same instance at the same prices and seed produce
     identical schedule hashes.

## 3. Task 1 — Synthetic price-response outer loop (Phase 1)

Price map: affine inverse supply per hour, `p_t(L_t) = a_t + b_t * L_t`,
with base load folded into `a_t`. Calibrate `a_t` to the instance's existing
tariff and sweep `b_t` as a market-depth parameter (include b=0). Add a
smooth nonlinear map (e.g., quadratic or exp) and a piecewise-linear step map
as secondary cases once the affine case is complete.

Implement `src/outer_loop.py` with these regimes:

- **R-EXO** (baseline): solve the EVSP once at fixed prices `a_t` (b=0).
- **R-ITER** (naive chicken-and-egg): `p^{k+1}_t = a_t + b_t * L_t(S^k)`;
  re-solve; repeat. Undamped.
- **R-DAMP**: `p^{k+1}_t = (1-alpha) * p^k_t + alpha * (a_t + b_t * L_t(S^k))`
  for alpha in {1.0, 0.5, 0.25, 0.1}. (alpha=1.0 reproduces R-ITER.)
- **R-STRAT** (milestone 2): strategic fleet minimizing its own bill
  `sum_t p_t(L_t) * L_t + c(S)`. Solve by sequential linearization: at the
  incumbent load, post marginal-outlay prices
  `p~_t = a_t + 2 * b_t * L_t^k`, solve the EVSP, damp, repeat. Label the
  result "stationary point under linearization," never "strategic optimum."
  Optional add-on: exact strategic optimum over the current column pool via
  a pool MIQP — label it "finite-pool strategic optimum."
- **R-DICT** (milestone 2): planner minimizing
  `c(S) + sum_t [a_t * L_t + b_t * L_t^2 / 2]`. Same sequential
  linearization with prices `g_t = a_t + b_t * L_t^k`. Note (and verify
  empirically): R-DICT's stationarity condition coincides with an R-ITER
  fixed point — a converged naive loop IS a stationary dictator solution.
  Log this comparison explicitly.

Two-fidelity policy (mandatory): use re-realization + restricted master for
inner iterations. Invoke the exact expanded pricer only (a) at declared final
candidates, (b) when the outer objective stalls, or (c) on cycle detection.
Record tier for every solve.

Cycle detection: hash the pair (schedule hash, price vector rounded to a
declared tolerance) each iteration; classify runs as fixed-point / 2-cycle /
n-cycle / non-repeating within an iteration cap (default 50). **Never report
price convergence as schedule convergence** — log and report the two
separately.

Sweeps: b_t magnitude (at least 5 levels from "fleet negligible" to "fleet
dominant"), fleet multiplier if the oracle supports it, alpha, price
initialization (tariff vs perturbed), and both instances (k=8, k=13).

Acceptance tests (AT-1):
- with b=0, R-ITER terminates in one iteration and matches R-EXO cost
  exactly;
- every final schedule is replay-validated by re-realization at the final
  prices and matches the reported cost within tolerance;
- at least one full sweep completes end-to-end producing one tidy results
  CSV in `result/` plus per-run JSONL logs;
- a summary table reports, per (instance, b, alpha, regime): final cost,
  bill, true generation cost, iterations, convergence class, oracle tiers
  used, wall time;
- the R-DICT-stationarity vs R-ITER-fixed-point comparison is reported for
  every converged run.

## 4. Task 2 — Switch-boundary mapping (Phase 2)

Purpose: measure how often small price changes flip the discrete schedule.
This single statistic decides whether the machine-learning direction of the
thesis lives or dies, so precision matters more than coverage.

Implement `src/switch_map.py`:

1. Start from the R-EXO solution at calibrated prices. Perturb one hour's
   price at a time over a grid, then refine each detected switch with
   bisection to a declared precision `delta_min`.
2. At each evaluated price point, record: whether the optimal trip-sequence
   set changed (via schedule hash), change type (`charging-only` |
   `trip-sequence` | `fleet-size`), objective margin to the incumbent
   schedule, and load discontinuity size |delta L|.
3. Use re-realization + restricted master for the grid; confirm each located
   boundary with one exact-pricer solve on each side (tier-labeled).
4. Output: a switch-map CSV per instance + a plot of stability intervals per
   hour, in `result/`.

Acceptance tests (AT-2): boundaries located to `delta_min`; each confirmed
boundary has exact-tier solves on both sides; summary reports the fraction of
price space (per hour) where the response is charging-only vs combinatorial.

## 5. Guardrails

- No pushes or merges to `egg`'s remote without Nathan's review.
- No modifications inside EVSP-DR; wrapper only; pinned-commit check on
  every run.
- No ML, no mechanism design, no multi-fleet, no new pricing algorithms —
  out of scope for this handoff.
- Honest-labeling table (from the historical handoff, Section 7.4) governs
  all reporting language:

| Result | Only permitted label |
|---|---|
| Old charging events re-costed | Exposure of a fixed realization |
| Fixed trip sequence re-realized | Exact charging response for that sequence |
| Restricted pool re-optimized | Finite-pool optimum |
| Capped/limited DP | Heuristic duty response |
| Expanded pricer completed, no negative reduced cost | LP certificate on the discretized route space |
| Pool MIP solved | Integer optimum over the current pool only |

- Every reported number in any summary must be traceable to a JSONL record
  (include the record path or hash in the table).
- Prefer boring, deterministic code; fixed seeds; no cluster (Unicorn) runs
  in this handoff — local `k=8`/`k=13` only.

## 6. Milestones and order

1. **M1**: Task 0 complete (ORACLE_API.md + runlog + AT-0 green).
2. **M2**: Phase 1 regimes R-EXO / R-ITER / R-DAMP with the affine map,
   full sweep on k=8, then k=13 (AT-1 green except R-STRAT/R-DICT rows).
3. **M3**: R-STRAT and R-DICT added; the stationarity comparison reported.
4. **M4**: Phase 2 switch map on both instances (AT-2 green).
5. Stop and hand back. Do not proceed to stabilized-master work (du Merle /
   bundle) without a new handoff — that is the flagship paper's code and its
   design will be specified separately.

Open questions to surface to Nathan rather than resolve unilaterally:
terminal-SOC policy, charger-capacity assumptions, station-to-node mapping
for the price map, and any EVSP-DR interface ambiguity found in Task 0.
