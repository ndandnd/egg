# Focused supervision repair proposal

23 October 2026. This is the next implementation package, not a native retry authorization. Preserve v1 source, lock, fixture, failure and all169.35673816793766s of cumulative charge.

1. Replace independent80ms monitor timeouts with one explicitly bounded sample deadline inside the existing <=0.25s sampling policy. Retain the actual timeout command, allocated timeout and primary stop reason. Fail closed when the complete sample cannot be obtained. Do not silently relax the resource policy or infer that missing data were healthy.
2. Treat a process-group existence `PermissionError` as unknown, not absent. Use bounded cleanup/probe state, retain the diagnostic, and confirm eventual absence or produce an unresolved cleanup failure. Preserve observed owned-group identity and parent-death protection.
3. Make terminal cleanup/receipt processing idempotent. A secondary cleanup exception must not replace a primary monitor failure with a fictitious interruption. Retain both causes and complete conservative accounting even when finalization is partial.
4. Add solver-free regressions for monitor timeout attribution, the existence-probe permission race, cleanup retry/idempotence and primary-cause retention. Do not rerun unrelated qualification tests without a reason. Any new checked revision needs an explicit resource allowance and immutable result receipt.

After reviewed checks, prospectively freeze a new qualification revision with the same identity-selected40/80 cases, source hashes, actual final ledger charge and a new output namespace. A deliberate native rerun must be explicitly recorded as a repaired revision, preserving the failed first task and its spend. No case replacement, automatic retry, longer solves or comparison screen is authorized by this proposal.
