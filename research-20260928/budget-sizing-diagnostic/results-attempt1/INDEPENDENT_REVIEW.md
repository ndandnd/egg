# Independent result-integrity review

**Pass: the bounded eight-cell result is internally consistent.** This review checked the sealed manifest, frozen design, receipts, assessments, summary, supervisor/wrapper receipts, source hashes, and scoped Slurm accounting. It did not read or reproduce raw event contents, run a solver, or reinterpret the native certificate method.

The private collected tree has an exact 63-file manifest inventory; all 63 byte counts and SHA-256 values match, with no missing or extra files. The published subset intentionally contains the manifest and selected immutable receipts/summaries rather than all 63 raw files. Its copied manifest, frozen design, summary, supervisor receipt, wrapper receipt, and `sacct` record match the collected originals. The frozen design declares eight unique cells covering both markets × call caps 4/16 × bit caps 4096/8192. All 12 frozen source-file hashes match the reviewed source tree; the supervisor reports return code 0, stable seal, quiescent process group, and unchanged hashes.

All eight launch receipts are on time, return code 0, and use the declared 90-second cap. Each raw/result envelope matches its frozen state and cap; all eight assessments have complete evidence and reconcile to the native result bounds, and the summary's exact lower/upper/gap fields match the raw certificate and mixture. Pricing and master component timings are marked complete in all eight rows.

| Market | Cap cells | Outcome and observed work | Maximum bits | Global gap (approx.) |
| --- | --- | --- | ---: | ---: |
| Original | 4 calls, either bit cap | Budget exhausted at 4 pricing / 4 masters | 271 | 4.072023 |
| Original | 16 calls, either bit cap | Certified at 5 pricing / 4 masters | 271 | 0.000001 |
| Changed | 4096 bits, either call cap | Bit-limit stop at 3 pricing / 3 masters | 3974 | 4.871380 |
| Changed | 4 calls, 8192 bits | Pricing/time stop at 4 / 4 | 7752 | 2.929457 |
| Changed | 16 calls, 8192 bits | Certified at 6 pricing / 5 masters | 7752 | 0.000001 |

Pricing-request totals include the seed call. At the two 16-call/8192-bit cells, the stored exact gaps are about `1e-6`, below the configured `1e-4` tolerance. Thus cold runs certify after five total pricing requests in the original market and six in the changed market, at the relaxed 16-call/8192-bit setting. These are native solver outcomes for this development case, not an exact ideal-model floor: exact replay of stored numbers does not remove Gurobi pricing-bound tolerances.

Time accounting reconciles: child receipts span 2.788–3.700 s; wrapper elapsed is 48 s, including 17 s freeze/preflight/setup and a 27.51 s supervisor interval; Slurm reports 51 s total, exit `0:0`, one CPU, 8 GB, and 122700K maximum RSS. Component solver times are reported separately from child wall time and are not summed as end-to-end time. The run is one deterministic development diagnostic and supports no general speed or scalability claim.
