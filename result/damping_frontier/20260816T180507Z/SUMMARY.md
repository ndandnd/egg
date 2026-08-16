# Run summary: `runs/overnight/20260815T033012Z/damping_frontier`

Total records: **26598**
- backends: {'GRB': 26598}
- statuses: {'OPTIMAL': 26598}
- git commits: {'7a70500': 21778, 'fe2f229': 4820}
- replay_ok (raw stored): {True: 26435, False: 163}

## Replay status (raw is never hidden)
- raw legacy replay failures: 163
- successfully revalidated: 163
- unresolved replay failures: 0
- revalidation sidecars present: 163 (nonaccepted: 0 — only certified_equivalent resolves; alternative realizations are diagnostic and NOT accepted)

## Checkpoint completeness (expected-count gates)

| type | expected | found | complete | missing |
|---|---|---|---|---|
| cell | 288 | 288 | 288 | 0 |
| loop | 288 | 288 | 288 | 0 |
| sweep | (not gated) | 0 | 0 | - |

## Phase-1 loop outcomes (price-state detection) by (b, alpha)

| b | alpha | fixed_point | cycle | max_iters |
|---|---|---|---|---|
| 0.01 | 0.05 | 1 | 3 | 12 |
| 0.01 | 0.1 | 1 | 12 | 3 |
| 0.01 | 0.15 | 1 | 14 | 1 |
| 0.01 | 0.2 | 1 | 15 | 0 |
| 0.01 | 0.25 | 1 | 14 | 1 |
| 0.01 | 0.35 | 1 | 15 | 0 |
| 0.01 | 0.5 | 1 | 15 | 0 |
| 0.01 | 0.75 | 1 | 15 | 0 |
| 0.01 | 1 | 1 | 15 | 0 |
| 0.05 | 0.05 | 0 | 0 | 16 |
| 0.05 | 0.1 | 0 | 2 | 14 |
| 0.05 | 0.15 | 0 | 12 | 4 |
| 0.05 | 0.2 | 0 | 12 | 4 |
| 0.05 | 0.25 | 0 | 15 | 1 |
| 0.05 | 0.35 | 0 | 16 | 0 |
| 0.05 | 0.5 | 0 | 16 | 0 |
| 0.05 | 0.75 | 0 | 16 | 0 |
| 0.05 | 1 | 0 | 16 | 0 |

## Solver statistics
- MIP wall time (s): median 19.75, max 472.80
- LP-vs-MIP absolute gap: median 301.255, max 700.038

## Audit verdict
**PASS** — expected checkpoints all present and complete; no unresolved replay failures; no nonaccepted revalidations; every solve OPTIMAL and certified.
