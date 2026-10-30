# Graph v6 bounded implementation review

Verdict: **APPROVE for the prospective bounded pilot**, with the source/environment
freeze and per-task execution-node probe gate required by the protocol. No
remaining substantive correctness, leakage, weighting, stopping, persistence or
CPU-budget blocker was found in the final reviewed package. This is permission to
run the declared exploratory experiment, not evidence of model or route benefit.

Reviewed30September2026: `physical_route_graph_v6.py`, training CLI, stdlib probe,
Slurm wrapper, graph fixtures and `ROUTE_MODEL_GRAPH_V6_PROTOCOL.md`, including
their v2/v3 input/weight/preprocessing interfaces. Review performed source reads
and tiny synthetic fixtures only. No exact128 model was fitted, no original or
new outer result was opened, and no job was submitted by this review.

## Correctness and data isolation

Graph topology comes from all declared case movements, not selected labels. Trip
vertices and separate depot source/sink vertices preserve parallel modes and
movement order. The admitted v3 adapter verifies immutable table/case identities,
TRAIN membership and source censoring before graph construction. Node features
are means of frozen edge inputs plus source/sink role flags; they contain no
selected-plan attributes. Every graph's node indexes are offset in a batch, and
both uniform and attention aggregation normalize within each node's own incoming
or outgoing neighborhood. The resulting message flow cannot cross source graphs,
timetable groups or partitions. Fixtures independently cover disconnection,
parallel movements, permutation equivariance, differentiable attention and equal
initial predictions for the two arms.

The pooled adapter materializes immutable TRAIN inputs/labels before partitioning;
isolation is enforced in `run_fold`. Only fit edges estimate mean/scale. Both
candidate models, selected fit/inner predictions and inner architecture promotion
are persisted before outer arrays enter scoring. The guarded-outer fixture
checks graph/features/labels access and fit-only preprocessing. All source/market
variants retain the inherited80/16/32 timetable split; the known missing source
is neither imputed nor silently granted extra weight.

## Weights, stopping and model evidence

Each movement receives `1 / (partition_timetables * observed_sources_in_timetable
* movements_in_source)`, matching v3. The formula is computed over the whole
partition before batching. Summing each batch's weighted loss gradients and
taking one Adam step per epoch therefore preserves the full-partition objective;
there is no per-batch rescaling or extra step. The fixture checks the paired/single
source weights. Parameter counts17857/17985 satisfy the18000 ceiling.

Stable logit BCE on inner groups selects the checkpoint; strict improvement and
fixed architecture order resolve ties. Outer metrics never participate in either
decision. Patience, epoch caps and soft deadlines are explicit. An independently
rerun time-cap fixture proves an interrupted second-epoch gradient is discarded,
no incomplete-epoch receipt is saved, and first-epoch selected weights are
restored. A task with no complete epoch fails instead of dropping an arm.

Numeric NPZ checkpoints use exclusive writes and `allow_pickle=False` loading,
with policy, architecture, exact tensor-name set, shape and finiteness checks.
Improvement checkpoints, selected weights, movement-keyed predictions and
promotion precede outer scoring. Final receipts hash all progress files. Tiny
roundtrip and selected-checkpoint tests reproduce predictions; complete campaign
replay remains required after collection, without refitting, before results are
admitted. Launch, typed failure and wrapper/probe evidence cover handled failures
and native import signals; a hard kill can still leave partial evidence as the
protocol explicitly allows.

## Runtime and bounded resources

The wrapper pins unicorn-cpu-75 and declares12tasks%4, one requested CPU,8GB,
30minutes, native thread limits1, no requeue and excluded scaglione-compute-01.
Its1700-second shared cap includes probe and training time; candidate750-second
and fold1650-second deadlines are soft and cannot expand that hard allocation.
Actual Slurm allocation is recorded separately. Code forces CPU float64,
one torch intra/inter-op thread and deterministic algorithms. No GPU or automatic
retry path exists.

The stdlib probe isolates import/operator/autograd/NPZ-replay stages in child
processes and flushes/fsyncs immutable receipt snapshots. A failed stage gates
TRAIN loading. The training identity now hashes wrapper, probe, isolated-runtime
receipt and dependency lock alongside scientific source. The Linux runtime's
official CPU wheel hash is recorded; login import success does not establish
node compatibility. Per-task probes on the allocated node remain prospective.
Separate gradient/update, fit/inner evaluation, epoch persistence, selected
prediction, aggregate progress-write and per-arm outer inference timers are now
present. Outer inference excludes feature/graph preparation and route decoding,
so it supports no end-to-end online speedup claim.

## Independent checks and limits

Final command:
`PYTHONPATH=src /Library/Frameworks/Python.framework/Versions/3.12/bin/python3
-m pytest -q src/tests/test_physical_route_graph_v6.py`.
**10passed in3.70seconds** independently. `bash -n
src/cluster/physical_route_graph_v6.sbatch` also passed. Local tests use
torch2.4.1/macOS and sklearn1.6.0; they do not qualify the separately pinned Linux
torch2.4.1+cpu/sklearn1.7.2 runtime. The protocol now states that allocation is
not runtime qualification and requires successful node probes before bank read.

Review-requested provenance and timing omissions were repaired before this verdict;
the final incomplete-gradient fixture passed. Full-data memory/runtime behavior,
Linux execution-node compatibility and complete saved-model replay are not yet
established. They are bounded experimental/runtime checks, not reasons to change
the frozen menu after viewing outcomes. Labels remain observed incumbent
membership; neither arm implies infeasibility, optimality or whole-fleet benefit.
