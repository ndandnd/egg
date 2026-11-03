# Independent launch review

**Disposition: no launch blocker after the bound-labeling fix.** The
protocol and runner declare 17 serial native-hull cells (10 training-group, 7
development-group), each with a 70-second native budget and 100-second child
cap; training is capped at 45 seconds, the controller guard at 2,100 seconds,
the shell timeout at 2,200 seconds, and Slurm at 45 minutes. The wrapper uses
one CPU, 8 GB, one thread per native library, `--no-requeue`, and excludes
`scaglione-compute-01`. There are no automatic cell retries. This remains below
the user's two-hour ceiling.

The learner's split guards bind timetable names and physical identities to one
base group and split. The 2004/2005 groups are reserved and are not materialized.
The development target input is rebuilt from the frozen design before its cold
label exists. Only training groups fit the model. The proposed topology is
projected onto replayed same-case whole-fleet plans; the learned arm passes that
plan through the same bounded native solver as its controls. The plan remains a
feasible proposal with unknown optimality; it is not described as an optimum or
as evidence of savings. Campaign and trainer receipts preserve failures, timing,
input/source identity, and output hashes. The exact cheapest control uses the
target nonlinear objective.

`label()` now gates trusted lower and mixture fields on the saved assessment
replay flags, and preserves raw values as `unverified_native_*` when no replay
was recorded. A focused regression guard covers failed assessment receipts.
Replay-checked individual feasible fleet labels remain usable as provisional
incumbents. Root reports the ten focused campaign/learner tests passed; I did
not run tests.

Review was static; no optimizer or cluster commands were run by the reviewer.
