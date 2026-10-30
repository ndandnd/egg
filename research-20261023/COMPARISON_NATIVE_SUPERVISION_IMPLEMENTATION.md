# Sixty-second comparison native preflight supervision adapter

24 October 2026. NEW `experiments.comparison_native_preflight` provides explicit
`freeze`, `run` and `analyze` CLI commands. No existing qualified source is edited.
Importing it does not construct fixtures or import a numerical backend. This is
candidate source/fake-test preparation; only parent may execute a prospectively
budgeted source-bound gate/freeze/native attempt after review.

## Reused supervision and restoration

`bound60(state=None)` takes a nonblocking process-local serialization lock and
restores every changed binding in finally, including exceptional exits. It binds
q.POLICY, OUTER_ALLOCATION=62.5, SUPERVISOR_STOP_S=61, launch,
completion_endpoint, verify_lock, freeze_accounting and _analyze. During run it
also wraps resume_state, finish and resource_step, delegating each to its saved
unchanged implementation. No concurrent in-process q use is permitted. The
reviewed q.run, finish, monitor/sample scheduling, STOP, ownership, cleanup,
postreceipt audit, ledger/resume and terminal CPU bodies remain unchanged.
Monitor-child CPU remains the actual q counter, charged once by q's existing
supervisor ledger. run corrects only the returned cosmetic planned8 to the frozen
two-task count.

`launch` reuses the entire saved q.launch ownership/FD/signal body. Within its
serialized scope only, a write adapter changes the attempt anchor deadline from
+30 to +60 and a Popen adapter changes the legacy worker module/subcommand to
`experiments.comparison_native_worker --lock --output --parent-pid --ack-fd`.
Both temporary functions restore even when spawning/materialization fails. The
new worker stays in its owned process group; detached group creation is not
permitted. Existing uncertainty/permission-denied probes remain failures.

The worker's physical/result/post-fsync acknowledgment endpoint is60. The
supervisor61 stop is a one-second exit/drain grace, not extra physical time.
Cleanup uses the original absolute anchor+62.5 cap. Completion validation checks
task, lock hash, parent anchor, exact60 deadline, result/completion hashes and
elapsed timestamps. The final worker-outcome artifact and its hash/status/
censored flag are bound by the only post-finalization acknowledgment. A
clock-failed/storage-failed/worker-failed outcome cannot be timely-valid. Unknown,
missing, malformed or late evidence remains failure/censoring.

## Frozen inputs and accounting

The fixed manifest has exactly two ordered tasks: engineering base50999/80,
seed17/day, cf1 first then recovery,60 seconds each. This reuses the same inspected
engineering timetable; it supplies no new independent sample or ML evidence.
`freeze --design --checks --accounting --lock` reads the explicitly designated
existing engineering fixture, verifies full identity/market hash, and derives
exact common-backbone/K restricted metadata. It never generates a timetable or
calls a solver. The GRB library is hashed without loading it. Source, asset,
passing-check, prior-account/evidence, environment, design and schedule hashes
are frozen. Worker verification additionally requires all thread limits1.

Freeze writes no provisional spend: freeze_charge_s=0 is unusable until an
external supervised freeze receipt is supplied to run. The separate parent
wrapper has7.5 seconds work/10 outer. Its required receipt binds policy/phase,
lock/source/prior-account hashes, successful exit, complete accounting, all
owned groups absent/reaped, no primary/secondary/monitor/cleanup uncertainty and
artifact/stdout/stderr hashes. charged_cpu_s is TOTAL, equal to allocation plus
supervisor CPU; cumulative is prior carry plus that total. Supervisor and monitor
costs are not added twice. The adapter carries the receipt's exact cumulative
difference forward. No new administration allowance is introduced.

Global1800 hard/1620 dispatch/180 shutdown policy is unchanged. A separate hard
230-second package starts at1296.29257734018 and ends1526.29257734018. Individual
40 check/10 freeze/125 workers/50 supervision/5 analysis figures are planning
provisions, not guarantees; unused provisions return to the aggregate cap.
Before launch the adapter requires actual accumulated spend plus62.5 allocation,
40 supervision and5 final analysis to fit. During resource updates it aggregates
resumed carry/freeze/prior ledger, unique newly finalized worker charges, active
maximum elapsed/tree CPU, supervisor CPU delta and q monitor-child CPU once. It
stops early when the aggregate plus2.5 cleanup/5 analysis reserve reaches the
package cap. Reentrant finish delegates keep original idempotency and never add
the same task's charge twice. Missing attempts/failure stop dispatch; no retry.

## Independent two-path analysis

Analysis uses the original serialized owner/ledger CPU finalization body and
checks immutable lock, freeze/run binding, resumed receipts/artifact chain,
strict completion/outcome ACK, RSS and engineering failures. It independently
replays fallback/selected witnesses and exact bills, checks durable fallback,
unrestricted bound scope/upper consistency and binary-only ordered start
mapping/inventory hashes. It reconstructs attributed start evidence from the
native log and requires processing for each of the two paths. CF1 additionally
requires its constructive charging proposal/fixed inventory and capture audit.
There is no old eight-task/fault/by-size gate or solver-round reconstruction.
Analysis CPU is appended after report creation; authoritative final accounting
must include that ledger tail, not merely the report's pre-analysis cumulative.

This does not itself qualify the sixty-second worker or prove engineering
success: actual prospective native qualification is still required. Even a pass
would establish only these two inspected engineering paths, not comparative
quality, optimality, speedup, generalization or learned-model value.
