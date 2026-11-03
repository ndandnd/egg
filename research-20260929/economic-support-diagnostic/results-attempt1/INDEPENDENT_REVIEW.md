# Independent result review

**Status: pass for bounded development-result admission.**

Job `597526` completed on `sonic-cpu-01.cs.cornell.edu`. The wrapper records exit 0, 174 seconds elapsed, 10 seconds for setup, and successful freeze, preflight and supervise phases; the supervisor records 161.58 seconds, exit 0, no timeout, a quiescent process group, a stable seal and unchanged source hashes. The allocation receipt records one CPU and 8,192 MB. The frozen commit is `41fa5f1e23833922292e2f70e346f386485aaa51`; all 23 frozen source hashes match the available checkout.

Manifest coverage is complete: all 97 listed payload files are present, with matching byte counts and SHA-256 digests. The summary accounts for all 6 cells and 12 stages. Each stage has an on-time, zero-exit receipt within its 210-second planner or 90-second response cap, and a complete certified assessment. All 12 child wall times and native solver wall times are present, and the native-time records are marked complete.

The six imported `CH` intervals match QP source job `595105`, commit `60a66e77be18e067aee4026f0e3a31dc120ec427`, and its frozen case and market identities. Its curated hashes match, all six source rows are complete, certified and on time, and its supervisor and wrapper receipts report successful completion. The new attempt uses those saved hull intervals; it does not rerun the hull stage.

I recomputed each `D−CH` interval from the planner and imported `CH` bounds and each own-price regret interval from the response bounds, saved prices, and the named planner's replayed load and operating cost. Exact rational arithmetic matches the stored summary, including the incumbent plan and price lineage.

| Services | Market | `D−CH` gap interval | Incumbent own-price regret interval |
|---:|---|---:|---:|
| 8 | source0 | [0.005249445, 0.005327351] | [0.149765675, 0.149767675] |
| 16 | source0 | [0.114493451, 0.114543451] | [0.432404769, 0.432406769] |
| 24 | source0 | [0.006730562, 0.006808118] | [0.128059603, 0.128061603] |
| 8 | target | [0, 0.000001999999986] | [0, 0.000001000000018] |
| 16 | target | [0, 0.000002000000065] | [0, 0.000001000000101] |
| 24 | target | [0, 0.000001999999957] | [0, 0.000001000000007] |

The source0 flat-market gaps have positive lower endpoints, while each target gap contains zero and has an upper endpoint around `2×10⁻⁶`. The source0 incumbent own-price regret intervals are concentrated around `0.14977`, `0.43241`, and `0.12806`; target regret intervals contain zero and have upper endpoints around `1×10⁻⁶`.

These are native solver intervals with physical-replay and solver tolerances; the stored rational endpoints do not turn them into ideal-model proofs. The evidence covers one seed-1006 synthetic development family. Its six cells are related cases, not independent test data, so these results do not establish performance on other families.

The check read the manifest, frozen identity, summary, supervisor and wrapper receipts, stage receipts/results/prices, and the imported QP collection artifacts. It did not inspect event JSONL files.
