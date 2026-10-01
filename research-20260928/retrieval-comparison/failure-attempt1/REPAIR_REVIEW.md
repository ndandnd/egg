# Preflight failure and environment repair review

**Verdict: the bounded environment repair addresses the observed failure; no retry is authorized by this review.** The original job 584876 failed before `native_probe`, supervisor, controller, or any scientific child. Its preserved wrapper receipt records preflight return code 1, wrapper return code 1, seven seconds elapsed/setup, and `timeout_exit: false`; the Slurm job ended `FAILED 1:0` after 12 seconds with one CPU and 8 GB. No supervisor receipt, controller marker, child directory, postmortem, or manifest was present, consistent with the wrapper stopping at preflight. The frozen login platform reported Linux kernel 6.8.0-136; the compute node reported 6.8.0-138; both were x86_64. This is an environment-preflight failure, not a solver result.

The repaired runner compares Python version/build, implementation and ABI tag, machine architecture, package versions, and Gurobi runtime across hosts. It records hostname and full platform/kernel separately, so the kernel-only difference does not reject the run. The effective native backend identity and model seed remain separately checked. Preflight now prints both host observations and the compared runtime before validation; mismatch errors identify differing field names. The focused test covers host/kernel variation, strict software/build, source-hash, and physical-design mismatch behavior.

The original failure remains immutable and is not converted into a successful attempt. No worker, native probe, optimizer, or new cluster submission was performed in this review. Root’s replacement decision remains proposed and not authorized; any future run requires the separate authorization and freeze specified by the protocol. Root reports the final nine pure tests passed (0.59 s), plus `py_compile` and diff checks; I did not rerun them.

## Reviewed pins

- `src/experiments/retrieval_comparison.py` — SHA-256 `74d2b1f634196ef6450620c9ebdda6421dde29ff03b92c0800afbf158689ed77`
- `src/tests/test_retrieval_comparison.py` — SHA-256 `35153e7e868b338c759d9566b4a1408abf8c539319efd195c0c5e074fe668598`
- `research-20260928/retrieval-comparison/RUNNER.md` — SHA-256 `77338fbf1e574c6b6576228e9ba05fa2239ea12b0ef1a33c7e4f33467af9e429`
