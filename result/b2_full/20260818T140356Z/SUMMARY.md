# B2 full-population analysis — 64 matched instances x A2-A5 (20260818T140356Z)

Analysis code commit: `71d4c378768a7c3a882a2236e9c2ce92d98e8b23`. Deterministic regeneration from the certified checkpoints (MANIFEST.json has every input and output hash).

## Population

- 256 method-cells: 64 instances x 4 methods (pilot 12 + 36 cells joined with the 208-cell expansion; exact union verified — no overlaps, gaps, or extras);
- certified: 256/256; two-call immediate-certification cells: 8 (verified, reported in two_call_cells.csv, never filtered).

## Method summary (overall)

| method | cert | median total calls | median clean | median stab | median wall (s) | W/T/L vs A2 (total) | clean W/T/L |
|---|---|---|---|---|---|---|---|
| A2 | 64/64 | 24 | 24 | 0 | 38.48 | — | — |
| A3 | 64/64 | 30 | 16 | 14 | 57.08 | 8/5/51 | 54/5/5 |
| A4 | 64/64 | 34 | 18 | 16 | 43.59 | 2/7/55 | 57/6/1 |
| A5 | 64/64 | 32 | 17 | 15 | 49.21 | 5/4/55 | 45/10/9 |

## Preregistered criteria (computed; true denominators)

| id | status | observed |
|---|---|---|
| acc-1-cert95-b005 | **pass** | a3: 32/32 (1.000); a4: 32/32 (1.000); a5: 32/32 (1.000) |
| acc-2-bound-sanity | **pass** | audits passed; min(z_D_ub + tol_d - LB_CH) = 0.01 |
| acc-3-stab-beats-a2-2x | **fail** | A2 median 24; best stabilized a3 median 30; speedup 0.800 (bar 2) |
| acc-4-vs-tatonnement | **not-testable** | no A0/A1 cells in the certified population |
| kill-1-a2-meets-bar | **pass** | A2 certified 32/32 on b=0.05 (rate 1.000, bar 0.95); acc-3 failed => kill ACTIVE |
| kill-3-zch-vs-dictator | **pass** | 0 contradictions; min margin 0.01 |

## b-stratified medians

| scope | method | total | clean | stab | wall (s) | cert rate |
|---|---|---|---|---|---|---|
| b=0.01 | A2 | 26 | 26 | 0 | 41.98 | 1.000 |
| b=0.01 | A3 | 43 | 22.5 | 20.5 | 53.43 | 1.000 |
| b=0.01 | A4 | 35 | 18.5 | 16.5 | 44.12 | 1.000 |
| b=0.01 | A5 | 45 | 23.5 | 21.5 | 49.30 | 1.000 |
| b=0.05 | A2 | 21.5 | 21.5 | 0 | 38.48 | 1.000 |
| b=0.05 | A3 | 27 | 14.5 | 12.5 | 60.22 | 1.000 |
| b=0.05 | A4 | 34 | 18 | 16 | 43.59 | 1.000 |
| b=0.05 | A5 | 27 | 14.5 | 12.5 | 46.59 | 1.000 |
| overall | A2 | 24 | 24 | 0 | 38.48 | 1.000 |
| overall | A3 | 30 | 16 | 14 | 57.08 | 1.000 |
| overall | A4 | 34 | 18 | 16 | 43.59 | 1.000 |
| overall | A5 | 32 | 17 | 15 | 49.21 | 1.000 |

## Verdict (computed)

acc-3 (2x speedup): **fail**; acc-1 (95% certification): **pass**; kill-1: **pass** (pass = kill signal active on the full population).

The scientific decision (stop stabilization and reframe vs a prespecified focused continuation) is recorded in doc/DECISION_LOG.md AFTER this artifact set is reviewed — this file reports the computed evidence, not the decision.
