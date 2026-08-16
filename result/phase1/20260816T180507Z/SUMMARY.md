# Run summary: `runs/phase1`

Total records: **4131**
- backends: {'GRB': 4131}
- statuses: {'OPTIMAL': 4131}
- git commits: {'cebe909': 2983, 'fe2f229': 1148}
- replay_ok (raw stored): {True: 4113, False: 18}

## Replay status (raw is never hidden)
- raw legacy replay failures: 18
- successfully revalidated: 18
- unresolved replay failures: 0
- revalidation sidecars present: 18 (nonaccepted: 0 — only certified_equivalent resolves; alternative realizations are diagnostic and NOT accepted)

## Checkpoint completeness (expected-count gates)

| type | expected | found | complete | missing |
|---|---|---|---|---|
| cell | 128 | 128 | 128 | 0 |
| loop | 128 | 128 | 128 | 0 |
| sweep | (not gated) | 0 | 0 | - |
- static-regime requirement per cell: >= 4

## Adaptive convex approximation (strategic/dictator)
- solves: 256; converged: 256
- gap abs: max 0.008789, median 0.002535
- rounds: max 15, median 5.0

## Phase-1 loop outcomes (price-state detection) by (b, alpha)

| b | alpha | fixed_point | cycle | max_iters |
|---|---|---|---|---|
| 0 | 0.1 | 8 | 0 | 0 |
| 0 | 0.25 | 8 | 0 | 0 |
| 0 | 0.5 | 8 | 0 | 0 |
| 0 | 1 | 8 | 0 | 0 |
| 0.002 | 0.1 | 6 | 2 | 0 |
| 0.002 | 0.25 | 5 | 3 | 0 |
| 0.002 | 0.5 | 5 | 3 | 0 |
| 0.002 | 1 | 5 | 3 | 0 |
| 0.01 | 0.1 | 1 | 4 | 3 |
| 0.01 | 0.25 | 1 | 7 | 0 |
| 0.01 | 0.5 | 1 | 7 | 0 |
| 0.01 | 1 | 1 | 7 | 0 |
| 0.05 | 0.1 | 0 | 2 | 6 |
| 0.05 | 0.25 | 0 | 7 | 1 |
| 0.05 | 0.5 | 0 | 8 | 0 |
| 0.05 | 1 | 0 | 8 | 0 |

## Solver statistics
- MIP wall time (s): median 1.99, max 542.92
- LP-vs-MIP absolute gap: median 127.401, max 682.776

## Audit verdict
**PASS** — expected checkpoints all present and complete; no unresolved replay failures; no nonaccepted revalidations; every solve OPTIMAL and certified.
