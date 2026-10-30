# Shared-clock coordinator: bounded solver-free checks

23 October 2026. This package implements the shared-clock coordinator required by `RECOVERY_QUALIFICATION_PROTOCOL.md`. It does not freeze or dispatch the eight-task native matrix, generate new timetable cases, fit a model, or establish a performance result.

## Scope and ownership

Create a new coordinator and focused tests; leave phase-0/core native sources and model assets unchanged. All six phase-0 attempts have terminal receipts. The scoped local process check on this wake found no matching EGG numerical worker. The three literature workers were completed before the implementation workers started. Record source hashes before each check attempt; no edits while a check runs.

The coordinator must preserve the supervisor's original monotonic anchor. The integer prefix cutoff is anchor+12s; physical prefix completion/lift must finish before anchor+15s. Full recovery may begin only before deadline−6s and only after explicit durable full-case fallback storage for a warm start. Its physical processing ends by deadline−3s; artifact finalization uses the final3s. No witness means a separately labeled cold full continuation with the actual remaining clock. No time means no new solver call.

Completion allowance is interpreted conservatively as **at most3s cumulative native fixed-topology completion across both stages**. A scoped, restored optimizer adapter may enforce this without changing the frozen native source, following the existing single-worker campaign's distinction between integer models and fixed-topology models. This adapter is for one serialized worker, not shared concurrent in-process calls. Test restoration on every exception. It does not qualify the operating-system supervisor, native start-processing evidence, or receipt endpoint by itself.

## Resource ledger

Carry forward phase-0 charge **66.880135CPU seconds**, supported by `native-primitive-v1/ledger.jsonl`, its six supervisor receipts and `RECOVERY_NATIVE_RESULTS.md`. Never reset this charge. Reserve a conservative **20CPU-second administration/review allowance** for this package's readback, source hashing, static review and accounting; it is an allowance, not measured utilization. Test-process allocations and check-supervisor CPU are additional.

Each solver-free check attempt has a30s wall allocation, one process group, one thread per numerical library, and5GiB sampled process-tree RSS limit. Sample at most0.25s apart and pressure at most1s apart; resource-monitor failure stops the attempt. Native backends must be mocked and never called. Record exact command, hashes, start/end, outcome, sampled CPU/RSS, process-tree termination, and conservative charge max(allocation elapsed, sampled CPU), plus check-supervisor CPU. A failed or interrupted attempt remains recorded; no automatic retry. Any repaired attempt gets a new name and source hashes. At most two checks are prospectively allowed for this package; a third requires a new stated reason/budget.

The900s cumulative qualification ceiling and720s dispatch stop remain in force. This package's initial total reserve is20+2×32.5s plus check-supervisor CPU; admission must still leave the original shutdown reserve. Exact phase-0 evidence hashes and completed check receipts must be carried into the future native phase-1 lock. No unused allowance authorizes a solver run.

## Required outcomes

Tests exercise actual coordinator integration with fake optimizer/clock/storage: import/preparation time charged to the inherited anchor; integer and fixed-topology native-call caps; completion spend shared across stages; explicit persistence before warm full dispatch; cold continuation without a prefix; no-time fallback; exception/replay failure retention; candidate bill recomputation; exclusion of restricted/fixed-route bounds; reversed full-bound visibility; and scoped-hook restoration. A passing package is implementation preparation only. The native matrix remains unqualified until separately frozen, executed and reviewed.
