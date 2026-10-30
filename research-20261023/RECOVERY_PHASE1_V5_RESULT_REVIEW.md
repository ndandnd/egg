# V5 engineering qualification: independent compact review

24 October2026. Reviewed gates, terminal ledger events, five supervisor receipts, compact result state and start evidence. No native event/value dumps, fixtures, models, sealed data, runtime imports, tests, solver calls or retries.

**Qualification failed: five of eight tasks terminal; three undispatched.** Four40-trip tasks completed without engineering issues. The80-trip static task failed physical-admission timing; dispatch stopped before80-trip recovery/cold/start-fault. This is engineering coverage, not ML or speedup evidence.

| Trips/arm | Endpoint seconds | Result/path |
| --- | ---: | --- |
|40 static|24.389853|Feasible retained physical witness|
|40 recovery|24.947448|Bounded; admitted fallback and one processed/accepted native start|
|40 cold|24.843467|Bounded physical witness|
|40 start-fault|12.790676|Expected setter fault exercised; admitted fallback retained|
|80 static|27.349969|No selected/fallback witness; control admission exceeded shared27s physical cutoff|

All five endpoints are uncensored and below30s. That does not excuse an overrun of the earlier physical-admission cutoff. The80-trip result records `TimeoutError` at control admission, `worker_failure:true`; it is an engineering failure rather than an ordinary unqualified no-incumbent endpoint.

Start evidence counts one submission, one processed start and one accepted start, all in40-trip recovery. Unattributed log matches are not additional submissions. Expected pre-build cutoffs remain visible separately from actual post-lift failure. Four admitted fallbacks and one retained-fallback fault path provide40-trip coverage only;80-trip warm-start/fault behavior remains untested. Gate audit reports zero invalid witnesses, mapping violations, bound-scope violations or censored endpoints. No result establishes a global certificate or learned-method advantage.

## Ownership and accounting

All five receipts record return code0 and confirmed owned-group absence:43665,44340,44893,45542,45851. The owner marker is absent. Receipts contain no secondary cleanup errors;45542 retains a transient permission-denied probe before subsequent absence confirmation. The receipts do not expose a separate `reaped` boolean; terminal return codes and completed owned cleanup are the available readback evidence.

Independently verified the complete ledger hash chain and each of five finish-record receipt hashes/charges. Authoritative recorded carry is:

- Prior qualification/check carry:721.7986948764081s.
- Externally supervised freeze charge carried in ledger:1.720336292723232s.
- Five task charges:117.299747458659111s.
- Run supervisor/monitor charge:71.13189399999966s, including7.123589s process CPU and64.00830499999967s monitor-child CPU.
- Final analyze ledger charge:.9415899999999999s.

Total **912.8922626277901s**, with no reset or additional administration. Monitor CPU is already included in the run-supervisor event; do not add it again. Gates'912.8892966277901s was materialized before the final analysis tail and understates recorded terminal carry by approximately.002966s. Use the final ledger total for authoritative accounting.

Ledger file SHA256: `dd592339fc722541dc5ba191b4bb14b5f813cb8947160ea0204a4355c2a33fb7`; terminal event hash: `9efde4c74eb052908c37ffc93af7e07b713c11a1ef6b02d9e3787321c8dc24d4`. Preserve this failed revision and undispatched suffix; no further native/check retry follows from this review.
