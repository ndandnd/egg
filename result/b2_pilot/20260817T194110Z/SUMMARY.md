# B2 pilot closeout — certified A2 vs A3/A4/A5 (20260817T194110Z)

Analysis code commit: `8c917e6ce9f3ecdf0a63fff9642935a1a8cf7e37`. All numbers regenerate deterministically from the certified pilot checkpoints (see MANIFEST.json for input hashes).

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
