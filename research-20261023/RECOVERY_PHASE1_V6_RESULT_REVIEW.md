# V6 engineering qualification: independent terminal review

24 October2026. Compact gate/result/start-evidence and terminal-ledger review only. No runtime imports, tests, native workers, raw-value dumps, fixture/model contents, source changes or retries.

**Qualification failed after2/8 tasks.** The run summary records `attempt_failure_stops_dispatch`. All numerical tasks used the80-first order; four40-trip tasks and80-trip cold/start-fault remain undispatched.

| V6 path | Observed outcome |
| --- | --- |
|80 static|Clean feasible witness; endpoint25.45105487573892s|
|80 recovery|Valid earlier fallback retained; one partial start submitted, processed and accepted; endpoint26.63527891691774s; full planner returned after25s handoff, recorded `TimeoutError` and `worker_failure:true`|
|80 cold/fault|Not dispatched; fault-retention path unexercised|
|40 all four arms|Not dispatched in this revision|

Both completed endpoints are uncensored under30s. A timely final artifact does not excuse the earlier handoff failure. Recovery's feasible retained witness and accepted native start establish those interface observations only; they do not make its full phase clean or complete qualification.

Gates report zero admitted invalid witnesses, mapping violations, bound-scope violations and censored endpoints; two fallbacks and one accepted/processed submission; zero exercised injected faults. Native processing and fault coverage are global-any checks in the executable gate, not per-size completion certificates. Here even global fault coverage is missing, and per-size coverage is explicitly incomplete. Prior revisions'40-trip successes cannot be silently combined with changed V6 behavior into an eight-task pass. No learned ranking inference, ML speedup or comparative performance conclusion follows.

## Owned termination and complete recorded spend

Both supervisor receipts record return code0, confirmed group absence and no secondary cleanup/probe errors. Owned PGIDs are54029 and54551; the run owner marker is absent. Receipts expose terminal return codes rather than a separate `reaped` boolean. CLI exit0 is not a qualification pass.

Independently verified the complete ledger hash chain and both finish-record supervisor hashes/charges. Terminal accounting components are:

- Carried prior spend:918.9402588373949s.
- Externally supervised freeze charge carried in ledger:1.854690583407887s.
- Two attempt allocations:53.358873916789890s.
- Run supervisor charge:28.91248000000007s, already including3.179796s process CPU and25.73268400000007s monitor-child CPU.
- Final analyze ledger charge:2.039088s.

The exact decimal sum of recorded fields is **1005.105391337592747s** (approximately **1005.1053913375928s** conservatively rounded). Use this terminal-ledger carry, not gates'1005.1015923375928s: the report precedes approximately.003799s of final analysis accounting. Do not add monitor CPU again, sum the gate report as another component, reset historical failures or add administration.

Ledger SHA256: `95aeeed35f07e305e57b8206a65a99bd0be091278a8d6a7722e0f81c9614a9cd`; terminal event hash: `055d56fdcca10ceceef5b912b30d12887808e35a255b4f189b6fb9abb5eeeb76`. Parent owns authoritative accounting. Preserve this failed revision and undispatched suffix; this review launches nothing.
