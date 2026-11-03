# Cold iterative solving: budget-sizing diagnostic

**Completed:** job 591255 returned all eight cells in 51 seconds. Cold solving
certified at five calls in the original market and six in the changed market
with the relaxed arithmetic limit. See [results and limitations](results-attempt1/RESULTS.md).
The original launch design and prior Doc update below remain historical.

This new development experiment isolates pricing-call and arithmetic limits on
the existing three-service multivisit case. Eight independent cold cells cover
both markets and the full four/sixteen-call by4096/8192-bit grid. It addresses
whether the earlier cap-dependent outcomes persist after relaxing either limit;
it is not a retrieval comparison or a claim of acceleration.

The [design](DESIGN.md) fixes all controls and interpretation. The new runner is
`src/experiments/budget_sizing_diagnostic.py`; its20-minute, one-CPU/8GB batch
entry point is `src/cluster/budget_sizing_diagnostic.sbatch`. No core solver,
historical attempt or pending retrieval protocol is changed. A new isolated
execution checkout and exclusive launch intent must identify any submission.
The batch wrapper records the runtime on the compute node before solving.

Read-only design inspection, from the repository root:

```sh
PYTHONPATH=src python -m experiments.budget_sizing_diagnostic design
```

Execution uses the declared `result/budget_sizing_diagnostic/20260928-attempt1`
directory once. Each child saves raw events, raw result, replay assessment and
elapsed receipt; the supervisor records all eight rows, including failed or
unstarted ones, and seals the finished files. A separate wrapper receipt includes
setup and total wall time. Lower/upper values remain native numerical bounds;
they are not ideal-model proofs. Missing component times remain unknown.

Root's final three focused pure tests pass, as does `bash -n` on the batch
wrapper and the working diff whitespace check. Sol also reports20 focused and
adjacent tests passing during implementation. No optimizer was run for these
checks. Independent review and launch/result receipts accompany the package
when available. Hosted checks are verified on the execution commit before
submission; no automatic retry or wider sweep follows.
