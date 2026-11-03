# V4 controller entry diagnosis

24 October2026. Source and compact metadata review only; no experiment imports,
tests, fixtures, models, captures, source changes or further native invocation.

The reported controller exit1 is explained by a floating-point representation
mismatch in the parent-preseeded carry-forward ledger. `resume_state` compares
the first event's `freeze_charge_s` with the canonical budget lock using exact
equality, before entering the worker-dispatch loop.

| Value | Seconds |
| --- | ---: |
| Frozen lock carried charge |1512.6011370494984|
| Freeze receipt cumulative charge |1515.7868660494985|
| Canonical difference used by `freeze_accounting` |3.1857290000000376|
| Preseeded ledger value copied from receipt `charged_cpu_s` |3.1857290000000003|
| Difference between those representations |0.00000000000003730349362740526|

`freeze_accounting` returns a budget lock whose freeze charge is cumulative
minus carried charge. Copying the receipt's direct charge instead produces the
observed exact-equality rejection: `Missing/corrupt cumulative carry-forward
ledger`. Both representations round to the same total after adding the recorded
external freeze reconciliation/closure0.614270999999917, namely
1516.4011370494984, but equality is checked on the component itself.

For any future separately authorized construction, the reproducible arithmetic
is the same expression used by the consumer, without weakening equality:

```python
canonical_freeze = receipt['cumulative_qualification_charge_s'] - lock['carried_charge_s']
carry_event['freeze_charge_s'] = canonical_freeze
external_freeze_tail = freeze_account['charged_cpu_s'] - (lock['carried_charge_s'] + canonical_freeze)
```

This is a diagnostic correction, not permission to modify this historical ledger
or rerun the package. Preserve the failed entry as recorded.

The current `runs` directory contains only `campaign.json` and `ledger.jsonl`;
it has no task directory or `.supervisor-owner`. Its three ledger events are
one carry-forward, one external-freeze-tail charge, and the controller's final
supervisor charge0.5440039999999999. There are zero launch or finish events.
This matches the source path: entry validation failed before launch, and the
`finally` block recorded supervisor CPU and removed the owner because no active
worker existed. No native worker was launched by this controller entry.

The external time observation is real0.98s, user0.38s, sys0.26s. Retain the full
entry cost with positive external reconciliation and closure in the final
account; do not charge only the internal0.544004s or discard this failed entry.
The source-check and metadata-freeze results do not establish CF1 mechanics.
This outcome is a controller accounting-entry failure, with the requested native
mechanism untested; it is neither CF1 infeasibility nor evidence of poor ML
performance. Stop this package under its no-retry rule.
