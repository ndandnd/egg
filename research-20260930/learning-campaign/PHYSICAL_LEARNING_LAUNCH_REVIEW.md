# Physical learning: first label-shard review

30 September 2026. This is a prospective review of the first training-only
64-cell shard. The subsequent launch receipt pins its execution commit.

The user has set manuscript drafting aside and authorized sustained dataset
collection, ML training and evaluation. The registry begins with 128 training,
32 development and 32 sealed test timetables; this job materializes only the
first eight training groups. No fitted model or development score is produced
by a data-collection job. Subsequent training sizes and route-proposal work are
described in LEARNING_SCALE_PLAN.md, rather than presenting the old two-source
selector as the final model.

## Physical and split review

Energy independently reviewed the generator and found an initial confounding
between depot access and battery-by-size combinations. Sol replaced the
assignment with a deterministic permutation of the full 54-combination factorial
before any native run or model outcome. The final bounded review found no new
blocker: battery upper and reserve map to the declared operating spans; driving
and auxiliary energy units agree; zero depot-idle draw is an explicit assumption;
depot thresholds filter existing opportunities; and train/dev/test identities
are separate. This review did not repeat the pure witness sweep or run a solver.

Sol's prelaunch validation includes a one-time physical replay of constructive
fleets for all 128 training cases. It does not materialize development or test
cases. Every first-shard input freezes its graph, witness hash, market identities
and physical metadata. The retained resources are one 90-kW connector, 90%
efficiency and a full terminal replenishment requirement.

## Runner and execution review

Root reviewed source/fixed-charge lineage, receipt/lock handling, budgets,
source/target case identity checks and result-label scope. Native source costs
are taken from independently replayed feasible columns; compatible verified
lower bounds are separate from relaxed-mixture upper values. Target labels
optimize a linear charging tariff and then rescore curved cost. They do not
certify minimum curved cost or a globally optimal physical fleet. The raw route,
movement, charging and failure evidence is retained for later structured learning.

The wrapper requests one CPU, 8 GB and two hours, exports one native/BLAS thread,
excludes scaglione-compute-01, and disables requeue. Sixty-four serial children
have 100-second caps, followed within controller/shell ceilings of 6600/6900
seconds. There is no model fitting or extra native qualification sweep. A fresh
checkout, absent-attempt check, submission sentinel and active-EGG guard protect
the single initial launch. No other project's jobs or held resources are changed.

After collecting this shard, check label completeness, physical replay, variation
between source plans and cost margins, then advance the planned training shards.
Scale concurrency only under a recorded subsequent resource budget. Do not turn
the first batch into repeated small-model tuning on old development examples.

## Completed prelaunch checks

Sol reports all 128 training constructive witnesses replayed successfully once,
without development/test materialization or native optimization. Eight focused
tests passed, covering factorial grouping, first-shard witnesses, units, split
exclusion, resource arithmetic, immutable paths, failed-source status and missing
source continuation. The final narrow worker guard rejects an off-shard request
before constructing its physical case. Eighteen source files are pinned.

```sh
PYTHONPATH=src python3 -m pytest -q src/tests/test_physical_learning_campaign.py
bash -n src/cluster/physical_learning.sbatch
git diff --check
PYTHONPATH=src python3 -m experiments.physical_learning_campaign design --shard 0
```

All commands passed. Root verified the final source scope and submission script.
Decision: publish and submit shard 0 once under the recorded ceiling.
