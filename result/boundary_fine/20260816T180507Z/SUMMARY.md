# Run summary: `runs/overnight/20260815T033012Z/boundary_fine`

Total records: **19264**
- backends: {'GRB': 19264}
- statuses: {'OPTIMAL': 19264}
- git commits: {'7a70500': 13920, 'fe2f229': 5344}
- replay_ok (raw stored): {True: 19264}

## Replay status (raw is never hidden)
- raw legacy replay failures: 0
- successfully revalidated: 0
- unresolved replay failures: 0
- revalidation sidecars present: 0 (nonaccepted: 0 — only certified_equivalent resolves; alternative realizations are diagnostic and NOT accepted)

## Checkpoint completeness (expected-count gates)

| type | expected | found | complete | missing |
|---|---|---|---|---|
| cell | (not gated) | 0 | 0 | - |
| loop | (not gated) | 0 | 0 | - |
| sweep | 64 | 64 | 64 | 0 |

## Phase-2 switch classification
- cells: 64 (0 incomplete)
- switches by kind: {'degenerate_tie': 2559, 'duty_change': 146, 'charging_only': 35}
- economic switches: 92 in 43 cells; margin-tied: 89
- load jumps (L1 kWh): median 35.5, max 195.8

## Solver statistics
- MIP wall time (s): median 1.14, max 64.57
- LP-vs-MIP absolute gap: median 84.842, max 209.390

## Audit verdict
**PASS** — expected checkpoints all present and complete; no unresolved replay failures; no nonaccepted revalidations; every solve OPTIMAL and certified.
