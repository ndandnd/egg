# Independent launch review: solver baseline comparison

Date: 2026-09-28

## Verdict

No remaining launch, resource-envelope, source-admission, cache-integrity, or paid-time accounting blocker found in the frozen 32-cell runner. The implementation preserves one serial case → arm → state-0/state-1 order, the specified solver controls and child deadlines, and explicit outcomes for ineligible, failed, timed-out, interrupted, and unstarted cells.

State-1 admission is limited to its own on-time state-0 source. The runner verifies source identity and replayable physical evidence, pins the raw result, assessment, child receipt, and pricing-event file, and rechecks those pins in the child. The final-arm cache path matches each cached bound to its original request/result/bound event and projection witness; the native runner re-evaluates admitted physical lowers under the target market.

Paid pair totals add both child receipt times and the dependent arm's parent admission check once. Missing child or admission timing leaves the total unknown. Source child time in the admission record is not double-counted. Partial reconciliation records malformed admission JSON, and malformed valid-JSON event shapes make only the dependent state ineligible.

The Slurm wrapper requests one CPU and 8 GB for two hours, excludes `scaglione-compute-01`, disables requeue, sets numerical-library thread counts to one, and applies the 6,000-second outer cap. Its elapsed timer begins at wrapper entry. Frozen runtime evidence includes Python/platform, MIP, Gurobi Python package and native runtime, SciPy, and NumPy versions.

## Review limits and validation

Review was static and read-only. I did not run tests, start native optimization, connect over SSH, or submit a Slurm job. The implementation agent reports 12 focused pure tests passing, plus a clean diff check and `bash -n`; the test source was inspected. The parent independently confirmed the final primary hashes.

## Final hash pins

| File | SHA-256 |
| --- | --- |
| `doc/SOLVER_BASELINE_COMPARISON_PROTOCOL_20260928.md` | `6e3005cf2b4e1801753c9189f2b01a7700c1fd074d62e2d38101b69765f6bc23` |
| `src/experiments/solver_baseline_comparison.py` | `5d2a02185d2850b58638459004118cb46df9c62703f00c93f4652361940d014b` |
| `src/tests/test_solver_baseline_comparison.py` | `76303f14c82e2d380a8077747fc5f671561d128da954b1bc7eab6ec861296e90` |
| `src/cluster/solver_baseline_comparison.sbatch` | `8f106855f96ba0d1ba251b6e4fd34656ddcf14348881fcb3798d95b0c13a7825` |
| `src/experiments/computational_benchmark.py` | `da96e4601e34dc797526703db68c2d2cbda57d78a9048c8fd7c34889ffca1c8f` |
| `src/egglab/native_hull.py` | `949de1551b4b6515860fdee7f63fd197c713c4645a7b20315802dd56712ada94` |
| `src/egglab/native_pathflow_hull.py` | `928676e25a6473d9c9874aed433db8434953f54b5c7a3ba3f84d596f717c4759` |
| `src/egglab/native_recharge.py` | `0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3` |
| `src/egglab/restricted_qp_proposal.py` | `466edb75dbd619feae37f423967cdd1068ec33abdcc70207fa01a006ba7b53dd` |
