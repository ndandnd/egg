# CF1 non-numerical monitor latency wrapper bindings

Source06 passed; the actual v5c metadata freeze failed when a process snapshot
exceeded its0.239720s deadline inside the15s work allocation. This was a monitor
latency failure. PGID8668 was reaped and absent; no lock or numerical worker was
produced. The old namespace, receipts and exact source06 bytes stay immutable.
`failed-monitor-accounting.json` retains cumulative2490.175941173126s and all
prior failures, with unknown historical actual CPU preserved explicitly.

New `run_cf1_resumption4_checks.py` and `run_cf1_resumption4_freeze.py` alone use
the non-numerical sample policy in `CF1_METADATA_MONITOR_DIRECTION.md`. Each
defines the same local, two-line `non_native_deadline` calculation:

```python
gap_end = work_end if last_completed is None else last_completed+1.25
return min(tick+1., gap_end, work_end)
```

Initial and subsequent complete process/memory samples share the resulting
absolute deadline. The process-sample timeout is at most1s; the completed-sample
gap is at most1.25s, and both are clipped to the phase's absolute work endpoint.
Polling remains0.05s. Late samples fail closed. Owned process registration,
detached children, sampled RSS cutoff, sampled/reaped CPU accounting, memory
pressure, cleanup and leader reaping logic remain intact. Resources are sampled;
the receipts do not establish an instantaneous physical memory bound during an
unobserved interval.

The source wrapper copies the reviewed source sample body locally to apply
only this deadline/gap change. The metadata wrapper changes its existing local
sample body in the same way. Neither mutates `recovery_qualification` production
monitor limits, native/controller freshness, live owner or native60/61/62.5
clocks. Native monitoring remains under its original0.25s policy. This decision
permits no numerical retry or weaker native admission.

The source07 phase starts at2490.175941173126 and ends2510.175941173126, retaining
work10/outer12.5/inclusive15/parent closure5. It requires a failed v5c freeze,
passing source06 and its immutable proof closure, actual external owned closure,
and incomplete historical observations. The sole affected test and eight hashed
dependencies remain unchanged. No old matrix or independent full hash audit is
added. Package275/end2701.723449631016 and global3000/dispatch2820/shutdown180
remain unchanged, with one thread/5GiB and the same inspected50997/40 CF1
seed17/day/no-fault mechanism.

The fresh metadata namespace is `cf1-entry-repaired-v5d`, requiring passing
source07 and dynamically reconciled `attempt07-accounting.json`. Metadata
work15/outer17.5/inclusive25 and worker62.5/entry7.5/supervision45/final30 funding
remain fixed. The local non-native sample policy is recorded in source/metadata
attempts, results, budgets, source command manifest, preparation receipts and
final accounts. The metadata design budget is the metadata manifest binding;
the freeze command remains the exact same-interpreter command list.

Source inventory binds both new wrappers, `manifest4-preparation.py`,
`freeze-preparation4.py`, `finalize-source07.py`, `finalize-freeze-v5d.py`,
`native-launcher-v5d.py`, this note, the monitor direction, approval4, accepted
guard, failed-monitor account, source06 accounting and raw v5c failure evidence
before source07. The new finalizers reuse source06 immutable snapshots and
retain dynamic carry, exact prior-plus-current sums, canonical lock/receipt
evidence, unique positive owned PGIDs and `hard_total_ceiling_s=3000` in the
postfreeze account. Default10/scoped17.5 consumer limits remain unchanged.

All preparation/preservation/closure remains charged. Static preparation runs
no project imports, tests, hashes, metadata command, native launch, cluster work
or commits. The parent reviews the stable bytes and freezes the exact command
manifest before one actual gate. Passing source alone establishes no lock,
owner/native timing success, feasibility, model quality or economic result.
