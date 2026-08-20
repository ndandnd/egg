# Local-move column proposer — bounded tiny result

Disposition: **HONEST-NEGATIVE**.

The frozen score counts only strict negative-reduced-cost, novel columns that pass independent physical replay.

- Cells: 6
- Clean-prefix snapshots: 38
- Global improvement opportunities: 32
- Captured opportunities: 0
- Capture rate: 0.000000
- Unique candidate partitions priced: 160
- Feasible/replayed candidate columns: 150
- Strictly accepted candidate columns: 0

| cell | snapshots | opportunities | captured | proposals | feasible | accepted |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `s0_n4_b0.01` | 6 | 5 | 0 | 24 | 24 | 0 |
| `s0_n4_b0.05` | 6 | 5 | 0 | 24 | 24 | 0 |
| `s11_n4_b0.01` | 1 | 0 | 0 | 8 | 3 | 0 |
| `s11_n4_b0.05` | 1 | 0 | 0 | 8 | 3 | 0 |
| `s15_n4_b0.01` | 10 | 9 | 0 | 40 | 40 | 0 |
| `s15_n4_b0.05` | 14 | 13 | 0 | 56 | 56 | 0 |

## Interpretation boundary

This is a four-trip synthetic mechanism spike conditional on the recorded clean-dual representatives and active supports. Structural changes, schedule hashes, wall time, and fixed-partition solver bounds are not scores. The proposer contributes no convex-hull certificate and no convergence or efficiency claim.
