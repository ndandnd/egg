# E11 protocol: solver-seed robustness of the main pruning comparison

Declared 2026-10-01 17:25 UTC. Every E3-E10 cell is a single run; MIP performance
varies with the solver's random seed, so the headline comparison must be repeated.

- Cases: scale 50000-50003 x {60, 80} trips (where the effects are large), `day`, T=60 s.
- Arms: cold, cold4, learned4 keep 0.15, learned4 keep 0.30 (v8 scores fold 0 / seed 17).
- Gurobi seeds 1, 2, 3 (`--grb-seed`, set on every model the planner/LP builds). The
  earlier runs used the solver default seed and are not re-labelled as seed 0.
- 96 runs, <= 3 concurrent, 16 GB. Report per case and arm: min/median/max bill over
  seeds, and how often learned4-k15 beats cold and cold4 per seed (paired by seed).
  Claim robustness only if the E3/E6 direction holds in the large majority of seed pairs.
