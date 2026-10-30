# Phase 0: native recovery primitive — 23 October 2026

Prospective only. Parent reviews and launches; preparing this specification/runner runs
no native optimization. Phase 0 plus every revision and later 40/80-trip qualification
share the **0.25 CPUh (900 CPU-second)** cumulative ceiling. The previously specified
40/80 matrix is phase 1, deferred, not today's launch. One worker, one native/library
thread, <=5 GiB process-tree RSS; no cluster, model scoring or sealed data.

`run_native_primitive.py` has `--freeze`, `--run`, `--analyze` and internal `--worker`.
Freeze ONLY after all integrated source edits/review settle. Freeze itself imports no
solver. Source hashes cover all experiment/egglab Python files, runner, this protocol
and original prototype fixture; verify before execution. Parent executes with the
worktree's native-enabled Python. No automatic retries: existing terminal attempts are
skipped; incomplete receipts block resume. A repair needs new lock/output with
`--prior-lock` and `--prior-output`; freeze locks prior receipt/ledger hashes and carries
all previous CPU charge. Never reset a revision to zero prior spending.

## Fixture and six exact tasks

The handwritten prototype fixture has trip `A` (0–60 minutes, 15 kWh), pullout `out`
and pullin `home`. Full movement order is `extra,home,out`; `extra` adds a 60–75-minute
alternative pullin which splits full charging intervals. The supplied physical witness
uses `out,home`, one vehicle, charging `home` 60–90 minutes at 15 kWh; fleet cost 7,
load [0,15]. No solver acquired this plan; its acquisition time is not an algorithmic
benefit and cannot establish route prediction efficacy.

All six tasks have one shared 30-second outer clock starting at parent launch anchor,
including imports, replay and artifact materialization. Ordinary search deadline is
outer deadline minus 6 s, reserving 3 s for completion and 3 s finalization. Native phases
are at most 3 s, at most two rounds. Completion shares the planner deadline. Search
exhaustion tests use an already-expired inner search deadline while the outer clock
still allows independent replay/finalization; they do not pretend replay costs no time.

| Immutable task ID | Target/action | Required outcome |
|---|---|---|
| source_normal | Source model, a=[1,2], b=[0,.2] | physical fallback bill 59.5, two binary starts [out=1,home=1], admitted terminal bill <=59.5 |
| full_normal | Full model, same market | full interval count greater than source; [extra=0,home=1,out=1], admitted terminal bill <=59.5 |
| changed_tariff | Full model, a=[0,4], b=[0,0] | independently recomputed fallback bill 67; terminal <=67, same physical lift |
| start_setup_failure | Raise at binary start attachment after durable full fallback | returned independently replayed bill exactly59.5; setup rejected; no native lower bound |
| expired_search_deadline | Full target with expired inner deadline | fallback exactly59.5; no model build/native optimize and no native lower bound |
| invalid_fallback | Change charge to10 kWh, expired inner deadline | fallback rejected; no returned plan, no native build/optimize and no lower bound |

For normal starts instrument native attachment: every binary receives exactly its
movement-ID value; continuous variables remain undefined; bounds unchanged. Native
verbose output goes to immutable per-task stdout/stderr. Report native acceptance only
when log text supports it. A log saying no new incumbent is rejection/nonimprovement,
not proof that a hint was infeasible. Unknown remains unknown. Submission alone cannot
pass the native-processing observation gate. Independent replay is a separate gate.

## Supervision, accounting and gate

Use existing platform `snapshot/tree_stats/memory_state` and owned process-group shutdown
utilities. RSS/CPU sample every <=0.25 s, system pressure every second; >5 GiB or <10%
free memory sustained5 s stops dispatch. Monitoring failure fails closed. SIGTERM/SIGINT
kill owned descendants; watchdog handles parent death. Outer supervisor kills at32 s
then0.5 s escalation; grace never admits a late endpoint. No numerical launch if the
whole32.5 s allocation would exceed720 charged CPU seconds, leaving180 s closeout.
Conservatively charge max(observed process-tree CPU, elapsed owned allocation) per task,
plus freeze/supervisor/analysis CPU. This overcharges sleeping/grace time rather than
silently omit descendants. Six tasks require180 nominal worker seconds. The initial lock carries a conservative
60 CPU-second preflight allowance for unmeasured solver-free tests/review/fixture
verification; this is a budget charge, not a claim of 60 seconds actual measured use.
The parent reports 57 fixed-core regression tests passed before native qualification.
Later revisions carry this allowance once through the prior ledger, without resetting it.

Every task writes immutable attempt, append-only native/resource events, fallback and
planner artifacts, final plan/replay where valid, result fsynced before completion marker,
and supervisor receipt. Marker binds result hash, lock, task and common parent anchor.
Endpoint uses finished materialization minus anchor, <=30 s. Missing/malformed marker
is censored; failed critical writes cannot produce an accepted receipt. Any missing
supervisor receipt blocks resume/audit, never counts as zero CPU or success.

Pass only if all six exact task expectations pass, endpoints timely, all receipts/spend
complete, resource limits met and at least one ordinary native start visibly processed.
Analyze reports unknown honestly and cannot invent acceptance from `model.start`.
No automatic phase 1 or economic-study launch. Solver-free fault/mapping/bound/clock
regressions in the broader qualification protocol remain required before phase 1;
phase 0 alone does not qualify that larger harness. Independent reviewer/parent should
inspect runner and integration regression results before freezing/launching.
