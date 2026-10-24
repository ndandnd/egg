# CF1 v5 sole source-gate failure diagnosis

24 October 2026. The sole frozen affected source gate failed and is stopped.
This diagnosis reads retained traces and the frozen new test source only. It
does not patch a bound source, import or parse project code, execute a test,
retry the gate, freeze metadata, prepare a real output or launch native work.

## Observed result

The retained `cf1-entry-repaired-checks/attempt01/stdout.log` reports
**26 failed, 16 passed, 36 subtests passed in 1.46 seconds**. Its result has
return code 1 and `passed: false`. The reported primary failure is pytest's
nonzero exit. PGID 71595 was absent and reaped, with no surviving groups,
cleanup errors, secondary errors or changed bound sources. These cleanup facts
do not turn the failed source gate into qualification.

The internal result charged 3.6579306243831518 seconds and reported cumulative
1531.493075714337 seconds. Those are the internal receipt figures, before the
parent's positive external-tail, closure and preservation reconciliation; this
note does not establish the final cumulative account or grant any credit.

## Exact failure category

Every one of the 26 retained failure traces has the same terminal exception:

`AttributeError: 'types.SimpleNamespace' object has no attribute 'cpu_count'`

The common path is the new test's `owner_harness` at line 148, then
`EntryClient.__init__`, then `_identity` at owner source line 114. The identity
condition compares `root.get('capacity_cpu_count')` with `os.cpu_count()`.
The handwritten fake OS at test line 124 supplies only `getpid` and `getppid`.
The handwritten owner root at test lines 135–138 also omits
`capacity_cpu_count`. The source review missed this fake-binding requirement.

| Affected owner test | Reported failing cases |
| --- | ---: |
| Actual final Popen command/expiry/binding/permit cases | 5 |
| Entry scope and restoration | 1 |
| Changed-root/late/unowned identity cases | 3 |
| Live guard baseline/staleness/reserve/package cases | 4 |
| Missing/incomplete/over-cap/unowned/changed/late permit cases | 7 |
| Fake parent process/argv/ready/cleanup test | 1 |
| Parent observation and suffix cases | 3 |
| Exact one-use precharge and real resume | 1 |
| Runtime status binding and sequence | 1 |
| Total | 26 |

The fake-parent-run trace has no second demonstrated production failure. It
fails while constructing `owner_harness`, before `OwnerSupervisor.run` is
called. Its intended process publication, generated argv, ready handshake and
retained missing-handoff receipt assertions were not reached.

## Coverage not established and prospective correction

The intended owner precharge, resume, permit, process-creation, parent lifecycle,
status and live-budget scenarios above were blocked during common setup. Their
positive and negative behavior is **not established by this invocation**. The
passing items in the summary do not establish full source qualification, actual
ownership/timing, real lock preparation, native entry or the CF1 mechanism.
Behavior beyond the failed setup remains unobserved; this diagnosis predicts
neither a clean rerun nor the absence of further defects.

A narrow prospective test correction would supply an explicit deterministic
`cpu_count` method on the fake OS and the same value in the independently
handwritten owner root before computing its digest. Adding the method alone
would leave the root binding inconsistent. Keep the production CPU-count check
intact. Any future correction needs its own prospective source decision,
immutable identity, budget and review; it must preserve this attempt, all frozen
source bytes, receipts and spending. No patch or new invocation is authorized
or performed by this diagnosis, and there is no automatic retry.
