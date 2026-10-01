# Independent bounded source review

**Disposition: pass for the bounded six-cell development diagnostic; no launch blocker found.** Its cases, source0/target markets, identities, alternating order, common budget, reserve, hard child cap, and controller cap match the reviewed cold native-LP baseline. I compared the 17 source hashes in the sealed baseline `frozen_identity.json` with current files; all 17 match. The case family remains nested development data, not independent test networks.

The sole execution-policy change is `master_policy=numerical_qp_proposal`, with denominator `10^9` and 500 proposal iterations. These values are frozen in the design, passed to `compact.certify` and `state_identity`, checked on return, and rechecked before bounds enter a summary row. NumPy and SciPy versions are added to exact runtime compatibility alongside the existing Python/MIP/Gurobi runtime and native GRB seed/backend probe. Source pins include the new runner, wrapper, tests, design, QP implementation, baseline runner, and relevant native dependencies.

The six-cell controller and partial reconciliation preserve all declared outcomes. Late, failed, incomplete, unknown-status, or policy-mismatched results do not promote bounds. Proposal count, non-success count, proposal time, and exact-replay time are retained from native counters; missing fields remain null. QP event traces do not turn absent native-LP master timing into zero: both native-LP time and completeness remain null, and applicability is false. Construction time remains unknown.

Timing caps match the baseline: six 210-second children plus 10-second TERM and 2-second KILL grace total 1332 seconds, within the 1500-second controller; the wrapper uses 1600 seconds and Slurm requests 1800 seconds, one CPU and 8 GB, with no requeue and the same node excluded. This is an exploratory single-seed method comparison. It does not promise certification or a timing benefit; reported bounds remain native and tolerance-conditional, not ideal-hull exact bounds. The implementer/root report the focused guards and shell syntax check passing; I did not run tests, an optimizer, or a cluster job.

## Reviewed source hashes

- `src/experiments/qp_baseline_diagnostic.py`: `0de2633d4eae278c5f12677b7cde3756c50d384a0c5df365033703cc052e4bf8`
- `src/tests/test_qp_baseline_diagnostic.py`: `6ce0e0dbaedd2b623feeb5b512afd6a5f24bbeec69810309a886a24bfc1d4123`
- `src/cluster/qp_baseline_diagnostic.sbatch`: `371298fdecebac44ab9e46c7dc448ccb126eac2cf6087a9932ab3fe9e50737c6`
- `research-20260929/qp-baseline-diagnostic/DESIGN.md`: `d53546bc9b71436abbd65189af8913e067e06a7ce223906d4b35062dc7030b87`
- `research-20260929/qp-baseline-diagnostic/README.md`: `968f493dd849c4056034a8b72804f0243ca84b7b385e95f314e8a3808591f39e`
