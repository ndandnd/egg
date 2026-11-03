# Native recovery primitive results — 23 October 2026

All six frozen tasks completed and passed their declared expectations. All three ordinary source/full/changed-tariff starts were processed and accepted in native Gurobi logs. The deliberately failing start attachment preserved the exact physical bill 59.5 without claiming a finite lower bound. The expired search deadline produced no model build or native optimization and retained the same bill. The corrupted fallback was rejected and no plan returned.

The two full ordinary cases have recomputed physical bills 59.5 and 67.0; their numerical full-model lower bounds are 59.499999 and 66.999999. The source-only normal result remains explicitly restricted in scope. These are tolerance-qualified native bounds, not exact mathematical optimality proofs. Binary inventory checks confirm all restored movement variables are free to change; starts contain no continuous variables and do not change bounds or row counts.

This is handcrafted engineering qualification only. No model was trained, no new route-performance comparison was run, and the 40/80-trip shared-clock campaign is not yet qualified. `RECOVERY_NATIVE_REVIEW.md` independently checks receipts/hashes and log evidence without rerunning the optimizer.

Resource accounting:
- Worker self-reported CPU: 0.433741 seconds (excludes interpreter startup and other processes).
- Conservative owned-allocation charge: 4.829848 seconds (wall allocation used when greater than sampled CPU).
- Qualification cumulative charge: 66.880135 seconds, including60-second preflight,1-second freeze and1-second analysis allowances, plus supervisorCPU. These allowances are not actual measured CPU.
- Largest timely endpoint: 0.238737 seconds.
- Largest worker self-reported peak RSS: 50282496 bytes; largest sampled process-tree RSS: 5603328 bytes. Sampling can miss brief peaks; self-reported and sampled measurements remain separate.
- Resource/monitoring failures: zero. All six process return codes zero. No retry or cluster activity.

The same900CPU-second qualification budget carries forward to subsequent qualification; no reset. Frozen source/fixture/protocol lock: `native-primitive-lock-v1.json`. Immutable per-task attempt/result/completion/supervisor receipts and phase logs are in `native-primitive-v1/`. Raw native stdout/stderr stay local; analysis records their hashes. The original October17 evidence is unchanged.
