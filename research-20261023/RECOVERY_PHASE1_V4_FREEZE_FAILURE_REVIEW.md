# V4 failed freeze: independent accounting review

24 October2026. Compact metadata/source review only; no fixtures/models read, runtime imports, tests, native dispatch or retry. The failed attempt and generated lock remain preserved; worker exit0 does not make this an admitted freeze.

## Recorded lower bound

The supervisor correctly records `passed:false`, `PermissionError`, unchanged sources and cumulative **612.3993446267449s**:

`610.9167105017234 carried + max(1.1598571250215173 elapsed, .46 sampled CPU, .67069 reaped-child CPU, .534856 worker CPU) + .322777 supervisor CPU`.

The maximum is elapsed, so this failed freeze adds1.4826341250215173s. The previous single20s package administration allowance is already included; add no second allowance. Attempt and stdout/stderr hashes independently match the receipt.

`RUSAGE_CHILDREN` is sampled before/after the supervisor's work and already includes its reaped monitor children (`run_recovery_freeze.py:122`,`:253`). Do not add .67069 child CPU, .534856 worker CPU or a guessed monitor amount again. Their difference .135834s is not a uniquely identified missing charge. The full worker record includes its reaped freeze subprocess, but cannot prove final CPU of a still-running watchdog.

## Ownership gap and reconciliation

Three resource samples identify **owned PGID37089**; their maximum recorded interval is .20506s. The worker endpoint was .59122s after anchor, leader exit observed .65533s, peak sampled RSS199,147,520 bytes. These establish observations, not final group absence.

The terminal `owned_pgids:[]/surviving_pgids:[]` is the initialized placeholder: `checked.cleanup` can raise before returning ownership, and its exception replaces the failure while losing that returned inventory (`run_recovery_freeze.py:236`; cleanup at `run_recovery_runner_checks.py:66`). Empty arrays therefore prove neither cleanup nor absence. A successful leader exit/reap does not retire its watchdog/descendants.

Treat612.3993446267449s as the recorded **lower bound**, pending the parent's OS/group reconciliation. Preserve PGID37089 and recover any available leader PID/reap state. Record confirmed group absence or bounded unresolved ownership, actual additional descendant/cleanup/OS-audit charges after the receipt, and conservative elapsed charging wherever final CPU is missing. Include previously unmeasured final audit work rather than inventing zero. If still unobservable, retain that uncertainty instead of calling the amount complete.

No numerical task may follow this failed freeze. Parent owns OS checks, reconciliation and any separately authorized repair; this note authorizes no retry or evidence overwrite.
