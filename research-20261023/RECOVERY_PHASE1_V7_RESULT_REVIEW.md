# V7 engineering qualification: independent terminal review

24 October2026. Compact gates, supervisor/result/start-evidence and terminal-ledger review only. No runtime imports, tests, solver/native work, raw-value traces, fixture/model contents, source changes or retries.

**V7 passes its recorded eight-task engineering gate.** All eight scheduled tasks are terminal; none are undispatched, censored or unresolved. The per-size coverage gate is true at both40 and80 trips: normal recovery processed a partial start with an admitted fallback, and the injected setter-failure path retained its fallback. Two starts were submitted, processed and accepted—one normal recovery task per size. Both fault tasks exercised their intended path. All eight tasks retain an admitted fallback.

| Trips | Static endpoint | Recovery endpoint | Cold endpoint | Fault endpoint |
| --- | ---: | ---: | ---: | ---: |
|80|25.318093s|27.522494s|26.916834s|16.101316s|
|40|22.360253s|22.940247s|22.913122s|10.775487s|

All endpoints are below30s and uncensored. These output times are distinct from the earlier physical admission endpoints and planner targets. Gates report zero invalid admitted witnesses, mapping violations, bound-scope violations and censored outcomes. Ordinary method statuses are feasible or bounded, not certified optimal.

All eight supervisor receipts record return code0, confirmed owned-group absence and no secondary cleanup errors. PGIDs59297,59798,60336,60885,61203,61661,62127,62602 are retired; the owner marker is absent. Task62602 preserves a transient permission-denied probe followed by confirmed absence; it was not silently interpreted as absent while unknown. Receipts expose terminal return codes rather than a separate reap boolean.

## Complete cumulative spend

Independently verified the entire ledger hash chain and all eight finish-record receipt hashes/charges. Recorded components are:

- Prior spend, including the preceding source-bound check:1008.1796634630955s.
- Carried external-freeze charge:1.8770721249971984s.
- Eight worker allocations:179.510402752086521s.
- Run supervisor charge:98.92183500000094s, already comprising10.59521s process CPU plus88.32662500000094s monitor-child CPU.
- Final analyze ledger charge:4.623512000000001s.

Exact decimal sum of recorded fields: **1293.1124853401801604s**, approximately **1293.1124853401802s** conservatively rounded. Gates'1293.11033834018s precedes approximately.002147s of final analysis accounting. Parent should carry the terminal-ledger total, adding no second monitor charge, historical reset or new administration allowance.

Ledger SHA256: `3e10b5f41edf44ef1992d50eb0b7e2dca6a3bad98e9d1c92c0b6de47374406c5`; terminal event hash: `de5cd4d6e89bc5838a56ed3d773b13f769ef0229271299e7dbd3c1df9f9683d6`.

## Claim boundary

This qualifies the tested recovery interface/timing/fallback behavior on **two engineering timetables**, one40-trip and one80-trip case, each at seed17 with the frozen nonlearned rule and day tariff. The preceding213-case software check and these eight native tasks serve different purposes. This is not evidence of learned ranking quality, ML speedup, optimality, tariff/general-network generalization or comparative economic advantage. Earlier failed revisions remain failed evidence. Parent owns accounting/summary and any separately reviewed next work; unused budget creates no automatic run or retry.
