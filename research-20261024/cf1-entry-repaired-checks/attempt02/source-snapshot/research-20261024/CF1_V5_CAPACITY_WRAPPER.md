# CF1 v5 capacity source wrapper bindings

`run_cf1_entry_repaired_capacity_checks.py` is a new source-only driver adapted
from `run_cf1_entry_repaired_checks.py`. The prior driver, root command/budget,
attempt01, its preserved source snapshot, and closed receipts remain immutable.
The new driver binds exactly `cf1-entry-repaired-checks/attempt02` with exclusive
creation, revision 5 and policy `cf1-entry-repaired-v5`; it has no resume or
automatic retry path. Source preparation creates no attempt02 directory or
prospective command/budget.

The predecessor is explicitly the known **failed** source gate: root
`cf1-entry-repaired-checks/accounting-final.json` must report phase
`failed_v5_source_check`, `check_passed=false`, complete accounting, owned groups
absent and reaped, no native dispatch, metadata freeze, research-data analysis,
original-v4 retry or automatic retry. Its authoritative carry is
1534.2196428390087. Its full inherited proof closure is hash verified. The bound
attempt01/result.json must additionally retain attempt01/revision 5/policy,
`passed=false`, `source_changes=[]`, a reaped leader, absent owned groups and no
surviving PGIDs. These checks accept a closed failure as prior charged work;
they do not label it a pass or grant native clearance.

The new additional phase is 13 s ending 1547.2196428390087: ADMIN 0, work 8,
outer 10.5, inclusive 11 and parent finalization/closure 2. The original source-phase
hard end 1547.8351450899538 still binds, as does the overall prospective campaign
end 1702.8351450899538. Global 1920/1740/180 remains process-local. One thread and
5 GiB remain unchanged. Parent reconciliation must preserve the 2 s closure reserve
and both source-phase ends; no unused time extends the original source phase.

The only shared-monitor clock adaptation is the documented call
`reviewed.sample_owned(proc, groups, registry, anchor-2., last_completed)`.
The retained helper uses its anchor solely in `anchor+10.` for the sample
deadline; this binding therefore yields the real parent anchor+8. Its complete
sample-gap, owned-row/registry, RSS/CPU and memory logic is unchanged. The real
attempt anchor, elapsed and CPU accounting, ownership events and cleanup use the
actual parent anchor. Initial monitoring and launch/work checks use anchor+8;
cleanup uses anchor+10.5. Inclusive checks use carry+11 and parent closure 2.
The retained 2.5 s active finalization allowance and all monitor, ownership,
cleanup/reaping, output-audit and conservative charge mathematics are unchanged.
No historical helper is copied or edited.

Only `src/tests/test_cf1_entry_repaired.py` executes. The same eight qualified
historical tests remain hash-only dependencies, and the full current
`q.campaign.sources()` inventory remains bound. The retained fresh/source/owner
notes and monitor helper hashes are joined by `CF1_V5_CAPACITY_PROTOCOL.md`,
`CF1_V5_CAPACITY_FIX.md`, `CF1_V5_CAPACITY_REVIEW.md`, this wrapper note and the
new driver. New prospective files are exclusively
`cf1-entry-repaired-checks/attempt02-design/prospective-budget.json` and
`cf1-entry-repaired-checks/attempt02-design/command.json`; the parent creates them
after source review. The new command binds all inventory bytes except its own
digest, which the attempt records separately. Old root command/budget are only
historical evidence and are never used as the new prospective design.

The parent owns the whole-wrapper output/time logs under attempt02-design and
future consolidated `cf1-entry-repaired-checks/attempt02-accounting.json`, without
overwriting closed receipts. Failed, interrupted or incomplete new work stays
charged. This source check cannot authorize native execution, metadata freeze,
research-data access, a cluster dispatch or a retry.
