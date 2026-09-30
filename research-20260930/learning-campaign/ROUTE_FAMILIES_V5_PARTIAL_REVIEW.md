# Route families v5 partial completeness and accounting review

Launch `720831` was submitted on 2026-09-30 at 22:19:24 UTC for user `nc437`, Slurm name `egg-route-families128`, and array tasks 0–11. Its source commit is `75dd4cf19f1f735cc3dea559567da3b2bd32013e`; the pool manifest SHA-256 is `d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d`.

Tasks 2, 3, and 10 have task receipts with status `completed` and corresponding result files. Tasks 0, 1, and 4–9 and 11 failed with Slurm exit `4:0`; their stderr logs report `Illegal instruction`. Each of those nine task directories has `launch.json` and `source_identity.json`, but no task receipt or result. Their wrapper receipts preserve the launch identity (array ID, task ID, child job ID, pool hash, and CPU allocation) and Python return code 132, with timeout false. These are unreceipted Python ends, not absent or unidentified launches.

The table uses each array element's parent allocation row in `tmp/accounting-720831-current.txt`; it does not add the `.batch` and `.extern` step rows, which would double count allocation time. “CPU seconds” is allocation elapsed seconds multiplied by the allocated CPU count.

| Task | Outcome | Slurm elapsed (s) | Allocated CPUs | Allocated CPU seconds | Wrapper child elapsed (s) |
|---:|---|---:|---:|---:|---:|
| 0 | FAILED `4:0` | 13 | 1 | 13 | 5 |
| 1 | FAILED `4:0` | 11 | 1 | 11 | 5 |
| 2 | completed | 189 | 2 | 378 | 178 |
| 3 | completed | 119 | 1 | 119 | 113 |
| 4 | FAILED `4:0` | 7 | 1 | 7 | 3 |
| 5 | FAILED `4:0` | 7 | 1 | 7 | 3 |
| 6 | FAILED `4:0` | 8 | 1 | 8 | 3 |
| 7 | FAILED `4:0` | 8 | 1 | 8 | 3 |
| 8 | FAILED `4:0` | 9 | 1 | 9 | 2 |
| 9 | FAILED `4:0` | 9 | 1 | 9 | 3 |
| 10 | completed | 125 | 1 | 125 | 117 |
| 11 | FAILED `4:0` | 7 | 1 | 7 | 3 |
| **Total** | **3 completed, 9 failed** | **512** | — | **701** | **438** |

Summed task allocation elapsed time is 512 seconds, with 701 allocated CPU seconds (0.195 CPU-hours). Wrapper child runtimes sum to 438 seconds; weighted by each wrapper receipt's recorded allocation, they account for 616 child CPU seconds. Requested CPUs were 1 per task, but task 2 received 2 CPUs, as shown by both its accounting row and wrapper receipt. The launch's six-CPU-hour cap is 21,600 CPU seconds.

The numeric job ID `720831` has historical reuse, so it is not a sufficient accounting join key by itself. This review uses the current 2026-09-30 accounting identity—user `nc437`, name `egg-route-families128`, and array task identity—and excludes unrelated earlier records.

This is a completeness and resource-accounting review only. Model metric values were not inspected or aggregated.
