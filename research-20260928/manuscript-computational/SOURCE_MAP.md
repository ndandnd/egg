# Chapter evidence map

| Chapter content | Reviewed evidence |
|---|---|
| Table 1: scope and denominators; reserve versus feasible-pool narrative | `research-20260928/feasible-pool-pilot/results-attempt1/analysis/README.md`, `cells.csv`, `paid_totals.csv`, `paired_comparisons.csv` |
| Table 2 and Figure 1: all eight public target rows, open global intervals, failures and paid two-market cost | `research-20260928/solver-baseline-comparison/results-attempt1/README.md`, `analysis/cells.csv`, `analysis/paid_pairs.csv` |
| Within-run inherited-versus-fresh lower differences; component timing ranges | Same solver-baseline README and scalar cells; no failed cross-arm contrast is treated as a causal effect |
| Table 3 and Figure 2: four matched public fixed-price pairs; source-inclusive accounting | `research-20260928/pricing-start-pilot/results-attempt1/analysis/ANALYSIS.md`, `pairs.csv`, `source_costs.csv`, `accounting.json` |
| Quadratic source/target coefficients and horizon | `src/experiments/computational_benchmark.py`, market function |
| Linear and marginal fixed-price queries; cheapest-source anchor | `src/experiments/pricing_start_pilot.py`, `_bill`, `_choose`, `_queries` |
| Table 4: claim boundaries | Synthesis of the above; no new numerical evidence |

Figure inputs are SHA-pinned in `paper/latex/figures/FIGURE_SOURCES.json`.
The independent review pins the final chapter and its supporting source files.
Exact fractions in public CSV fields describe stored numerical evidence; they
do not turn native solver lower bounds into ideal-model proofs. Displayed lower
endpoints round down and upper endpoints up. Fixed-price effect labels use the
prespecified numerical tie threshold; source excess is relative to a returned
feasible incumbent, not an unknown optimum.
