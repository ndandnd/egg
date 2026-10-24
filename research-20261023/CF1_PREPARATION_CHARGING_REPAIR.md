# CF1 charging preparation repair

This source-only repair changes `src/egglab/constructive_charging.py`. The first native CF1 task entered charging at elapsed2.204s, froze its once-computed deadline at8.204s, and returned at20.392s without a fixed inventory or CF1 optimization. The saved evidence localizes the failure to pre-solve preparation, but does not measure an exclusive culprit: the old model event lacked a timestamp, and the provider rejected its late helper return before retaining the helper's detailed failure.

`_inventory` previously rebuilt `set(mapped)` for each model variable. It now creates that set once per inventory, builds the index lookup once, and reuses movement IDs/fixed values for the scalar ledger. It evaluates the immutable case identity once per inventory. There is no cross-call model, row or inventory cache.

Every existing physical audit remains: model/compiled identity; positive physical-row count; complete row signatures and row-count checks; original row-count condition; exact comparison against the preceding physical-row snapshot; unique variable/movement indices and cardinality; actual mapped variable identity and binary type; original0/1 bounds or exact selected fixed bounds; and continuous type for every unmapped variable. Each former inventory call still executes, before and after fixing/solving and before witness publication.

The compatible private interfaces add optional keyword callbacks:

```text
_row_signature(row, *, check=None)
_inventory(case,built,selected,physical_rows=None, *, check=None,measure=None)
```

`complete_topology` supplies its existing absolute deadline check. Traversals check at row entry/exit, every64 row coefficients, and each variable/movement/bound/unmapped iteration; binary fixing is checked per movement. A single native property access or Python sort is not preemptible, so these are cooperative bounds, not a claim of hard OS preemption. The post-operation checks still reject late work.

The additive `preparation_timings` list records scalar stages `validation`, `model_build`, `binary_fix`, and `inventoryN` with `.rows`, `.variables`, `.bounds`, `.unmapped`, `.ledger` substages. Entries contain monotonic start/finish, elapsed time, the unchanged deadline, `completed_before_deadline`, and optional error/clock-error diagnostics. Aggregate inventory intervals contain their substages; durations must not be summed as disjoint CPU charges. Timings remain in the helper result after deadline failure without requiring another deadline-blocked event callback. A failed final clock observation cannot turn a timing interval into successful work. The provider owner separately preserves these helper diagnostics before rejecting a late return.

The common60s allocation, once-frozen CF1 charging deadline, shared native quota, full physical replay, exact bill and late-witness rejection are unchanged. This repair does not establish that six seconds will suffice for this case, and does not reclassify the failed pilot. No runtime imports, tests, benchmark, fixture generation, solver or native execution were performed by the implementation agent. Parent review and one source-bound affected fake gate remain necessary; no native retry is part of this package.
