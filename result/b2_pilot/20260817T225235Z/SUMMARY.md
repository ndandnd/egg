# B2 pilot closeout — certified A2 vs A3/A4/A5 (20260817T225235Z)

Analysis code commit: `f64b7ce07b739aed81f6345e29874b532f5d9006`. All numbers regenerate deterministically from the certified pilot checkpoints (see MANIFEST.json for input hashes).

## Result

- 48 method-cells (12 instances x 4 methods); certified: 48/48; no budget exhaustion.

| method | median calls | IQR | median solver wall (s) | certified | W/T/L vs A2 (calls) |
|---|---|---|---|---|---|
| A2 | 21.5 | [17, 28.25] | 73.46 | 12/12 | — |
| A3 | 33 | [26, 42] | 61.66 | 12/12 | 0/0/12 |
| A4 | 29 | [21.5, 39] | 78.09 | 12/12 | 2/1/9 |
| A5 | 33 | [25, 57.5] | 60.76 | 12/12 | 2/0/10 |

## Interpretation (computed from the tables above)

A2 certified 100% of the pilot's b=0.05 instances with overall median oracle-call count 21.5; the best stabilized method (A4, median 29) gives a speedup ratio a2/best = 0.74, versus the preregistered acceptance bar of >= 2. On this pilot the STABILIZATION KILL SIGNAL (kill-1) is ACTIVE: memory (retaining all columns in the clean RMP) appears to solve the price-coordination problem that broke tatonnement, while du Merle boxes, Wentges smoothing, and proximal bundles do not deliver their preregistered speedup at this scale.

### Clean/stabilized call decomposition

A2 clean-call median: 21.5. Solver wall time is partitioned exactly once from solver-reported times (wall_clean_s + wall_stab_s = total_solver_wall_s, enforced).

| method | clean-call median | stab-call median | clean W/T/L vs A2 | clean-wall median (s) | stab-wall median (s) |
|---|---|---|---|---|---|
| A3 | 17.5 | 15.5 | 9/2/1 | 31.57 | 30.09 |
| A4 | 15.5 | 13.5 | 11/1/0 | 40.74 | 37.35 |
| A5 | 17.5 | 15.5 | 6/3/3 | 29.38 | 31.39 |

Stabilization — especially A4 — DOES accelerate clean-master convergence (see clean-call W/T/L), but its extra candidate calls are not amortized at this problem size: the total-call comparison still favors A2. The preregistered acceptance metric remains TOTAL oracle calls.

Denominators and caveats:

- 12 instances (seeds 0/11/15 x n 8/12 x b 0.01/0.05); the preregistered acceptance criteria are defined on their full populations — 64 moderate/strong instances per method for the 2x criterion, 96 b=0.05 method-cells for the certification criterion — so pilot evidence cannot pass or fail them, only support or reject continuing (see acceptance_status.csv).
- Stabilized iterations spend 2 oracle calls (clean certification + candidate) by design; the comparison metric is total calls to certificate, which is exactly what the acceptance bar preregisters.
- Each method-cell repeats its own dictator stage; dictator wall time is reported separately (dictator_wall_s) and excluded from solver-wall comparisons.
- A2 cells ran on the pre-stabilization checkpoint schema; broadcast metrics for them are recomputed from committed oracle prices (cross-validated where both sources exist).

## Next decision

Options on the table (DECISION_LOG.md):

1. Stop stabilization now and reframe Chapter I's algorithmic half around 'memory beats memorylessness' (equivalence theorem + uplift accounting + A2-vs-A1 budget-matched comparison).
2. Run ONLY the prespecified moderate/strong-feedback matched expansion (208 remaining A2-A5 method-cells) to give the kill decision its full preregistered denominator before abandoning stabilization.

The 960-cell campaign remains paused either way; the 576 fresh A1 baseline cells are a separate decision.
