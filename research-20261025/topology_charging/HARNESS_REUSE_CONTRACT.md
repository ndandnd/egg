# Thin serial harness reuse contract

25 October 2026. Source-only inspection of the needed local helpers and caller
boundaries in `warm_replication/run.py`. No case, receipt, model, raw log, label,
output or other data was opened; no imports, tests, hashes, generation, replay,
native work or solver calls ran. No new controller/monitor framework is proposed.
Parent confirmed that `scientific_common` was an imprecise pointer: the actual
source defines these helpers locally and imports no such module. Do not invent
that dependency or continue searching for one.

## Exact existing APIs and dependencies

| Callable in the existing file | Behavior/dependencies | Reuse decision |
|---|---|---|
| `save_new(path, value)` | Exclusive `x` JSON; Fraction→string; flush/fsync. Needs Path/json/os/Fraction. | May copy unchanged. |
| `publish(path, value)` | Exclusive owned `.final.tmp`, then `os.replace` over its owned incomplete placeholder. | May copy unchanged with save_new. |
| `load(path)` | Path.open/json.load of a supplied path. | May copy unchanged; caller must provide only admitted literal/owned paths. |
| `self_cpu()` | RUSAGE_SELF user+system cumulative process CPU. | May copy unchanged. |
| `children_cpu()` | RUSAGE_CHILDREN cumulative waited-child user+system CPU. | May copy unchanged. |
| `rss_bytes()` | ru_maxrss with Darwin bytes / other-platform KiB conversion. | May copy unchanged; observed peak, not instantaneous containment. |
| `resource_receipt()` | Own CPU, waited-child CPU, combined sum, observed self peak RSS/platform, prepublication scope. | May copy unchanged. |
| `launch_worker(root, output, spec, index)` | Fresh folder/spec/placeholder; one current-script child; bounded wait/cleanup; complete JSON read and external receipt. | Copy the narrow body pattern with explicit pilot identity/spec adaptations below; not callable unchanged for this study. |

References: [serialization/accounting helpers](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/run.py:87),
[launcher](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/run.py:633).
The helpers themselves need only standard library. The broader module sets
`PROCESS_WALL0`, `sys.dont_write_bytecode` and six numerical thread environment
variables to1 at import; it also declares the old cohort, scoring/model source
and asset paths ([header](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/run.py:1)).
Importing it is therefore unnecessary and carries unrelated global configuration.
Its scientific project imports occur within task functions, but invoking old
preflight/worker/campaign would bring the old generation/scoring workflow. Copy
only needed local functions into the new small caller, with their stdlib imports;
do not call the full campaign or bind an irrelevant model/source inventory.
The actual pilot's scientific QP/replay source closure is a separate freeze item.

## Launcher pattern to preserve

The existing launcher creates a fresh child directory and owned incomplete
receipt, writes the spec, then samples child/self CPU and captures a monotonic
anchor **before Popen**. It passes that anchor as
`--parent-anchor repr(anchor)` to a fresh `sys.executable CURRENT_SCRIPT --worker
FOLDER` process. STDOUT/STDERR are exclusive files, not unbounded in-memory pipes.
`start_new_session=True` and a preexec CPU limit apply. It checks one Python
thread before preexec; the worker is not permitted to spawn descendants.

For the pilot retain only the active-cell policy: child CPU hard90, inclusive
admission60 and native cutoff52. Remove the old acquisition150/120/90 branch.
Pass the remaining native allowance to the one QP operation; never interpret52
as a fresh limit after imports/model construction. All startup/imports, row reads,
model build/copy, optimization, extraction, independent replay and publication
consume the parent-owned60-second interval. The source worker defines these as
`end=anchor+60`, `native_end=anchor+52`
([worker clocks/check/stage](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/run.py:187)).

The parent waits only until anchor+60. Ordinary timeout marks late, directly
TERMs its still-unreaped Popen child, waits up to1 second, then KILLs/reaps within
the established3-second cleanup window. Exception cleanup likewise addresses
only that owned unreaped direct child; it does not signal historical/unknown
PGIDs. No retry or replacement process exists. This is a direct-child harness,
not a periodic watchdog, descendant monitor or new kernel-ownership mechanism.

After return, the launcher reads the **complete** worker receipt and updates
elapsed/CPU through that read. Admission requires reaped child, returncode0,
no timeout/launcher failure/fatal config, completed accepted worker packet, and
complete receipt read by anchor+60. A worker prewrite timestamp alone cannot
qualify. External-record publication remains paid to the parent campaign.
Preserve process-return time, complete-read time, late flag and failure details.

Necessary local adaptations are limited and visible: new script path/worker
entry point, new owned folder naming, frozen pilot spec/case identity, actual
preflight binding path and output schema. Existing `launch_worker` hardcodes
`__file__`, old kind/case_key/arm fields and an old preflight filename; using it
unchanged would dispatch the wrong work. Do not adapt by importing/scoring the
old arm menu. The check/stage/resource and stop/final-publication patterns may
be copied into the pilot worker without copying its scientific body.

## Cumulative package accounting and stopping

Use the existing cumulative funding pattern, not a sum of worker-reported CPU:
`self_cpu()+children_cpu()+unresolved_cpu_reserve+next_child_hard_cpu` must fit
dispatch funding. RUSAGE_CHILDREN covers waited children, so do not add the
per-worker waited deltas again to the parent cumulative total. Those deltas are
diagnostics. For any unreaped child retain its full90-second CPU reserve and
incomplete accounting; do not assume its missing CPU is zero or dispatch onward.
All timeouts, failed children, parent handling and finalization stay charged.
See [funding/limits](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/run.py:771).

Parent's selected new package is3600CPU/7200wall, dispatch3240 and reserve360,
with32 possible workers each conservatively funded at hard90. Preflight120 and
finalization120 are inside that package, not extra budgets; parent cleanup and
publication must also fit. The new caller must use its own constants/ledger,
not the old28800/36000 or old historical accounting prefixes. Freeze the wall
allowances explicitly: before a dispatch, require current elapsed plus next60,
bounded cleanup and the selected remaining finalization wall provision to fit
7200. No undeclared refill follows from insufficient funding.

The once-only bounded metadata cohort-selection record is part of paid preflight,
before original row access. It uses only the established assignment formula and
derived receipt group/base/stratum fields, as parent selected; it does not call a
case generator, score candidates or silently replace an inconvenient group.
Parent separately freezes selected IDs and the actual source/input command.

The parent process's RLIMIT_CPU bounds its **own** CPU, not own+all children;
cumulative own+waited-child observations and conservative dispatch funding supply
the combined package accounting. Whole-process external timing charges the
write/exit suffix once. Final receipt must retain all planned cells, including
unattempted cells after a stop, unresolved reserve/accounting completeness,
parent/children combined work, total elapsed and finalization observations.
The old finalization code demonstrates preserving a full assignment ledger
([closure](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/run.py:899));
copy that principle, not its384-cell acquisition/reference/model logic.

## One call, fallback and qualification are separate

Each admitted pilot cell permits one QP dispatch, never another solve after a
poor status, missing incumbent or late result. Preserve actual call count or
unknown dispatch status on exceptions. A previously admitted physical witness
may remain the operational fallback, but it is not a newly qualified QP result.
Keep fallback use, new physical candidate, numerical status/OPTIMAL, objective/
matrix/physics checks and parent-timely admission separate. A provisional valid
incumbent can be retained without claiming qualified optimal charging; raw
objective/status alone is not a feasible cost. No model-performance threshold
or new physical tolerance is implied by this harness contract.

The promised next review is one focused integration pass on the eventual small
caller, not another engineering matrix. This document authorizes no execution,
native call, data expansion, source edit to old files or numerical reservation.
