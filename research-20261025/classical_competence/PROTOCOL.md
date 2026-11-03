# Two-case offline classical competence — prospective protocol

25 October2026. This is a new offline diagnostic, not a retry of a historical
attempt, a matched performance study or qualification of the main CF1/recovery
controller. Parent review freezes this protocol and `run.py` before one run.
No production/helper/test source changes, new monitoring framework or new tests.

Exact cases, chosen without the new outcomes: `scale:50685:40` and
`scale:50605:80`, respectively the lexicographically first40/80-trip SCREEN
cases in the existing October17 manifest. Qualification cases are excluded.
Rebuild only these already inspected synthetic cases through `claude_cases.make`;
verify exact full case identities and movement order against the existing
`local-assets-v3.json` case mapping. Use the original day market. No protected
DEV/TEST/A6/B3/confirmation/GIRO, new training, model inference or cluster.

## Exact new command and limits

From the worktree, the sole child command is:

```
.venv-local/bin/python research-20261025/classical_competence/run.py --root /Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017 --output research-20261025/classical_competence/attempt01
```

The directory is exclusive-create. One Python process, no spawned worker or
watchdog, backendGRB, native budget threads1, numerical thread environment1.
Keep solver DEFAULT seed unmodified and record its numeric value as unknown:
this is not a seed17 paired performance result. No monkeypatch, optimizer hook,
Owner, permit, native-dispatch flag, recovery schedule override, pruning,
integer full search, automatic retry, reverse merge repair or cold fallback.

Total package240CPU seconds including imports, input verification, both cases,
events/replay/writes and closure; outer wall180 seconds. The script installs
CPU hard limit240 and wall alarm180, with cooperative225CPU/165wall body limits
to reserve15 seconds for closure. The parent meters the whole process and owns
the external hard stop. Python alarms/native solver time limits do not guarantee
preemption of a blocking native call. Keep observed process peak RSS<=5GiB;
record normalized bytes and platform raw units. Peak observations are not an
instantaneous memory guarantee. No separate native-control claim follows.

## Standalone physical procedure

The existing library API `constructive_charging.complete_topology` accepts a
caller-supplied absolute deadline. Its physical inventory, extraction, replay,
exact billing and status checks remain unchanged. A separately budgeted standalone
fixed-topology subproblem is legitimate library use; it does not satisfy the
registered CF1 construction/charging/recovery schedule and is not relabelled as
that experiment. The driver asserts the native optimizer is its original alias
and stops on unexpected hook mutation; it disables or replaces no guard.

For each case, start one60-second clock before case construction:

1. Rebuild and identity-check the full case. Call deterministic price-blind
   `constructive_control.construct_routes` once, deadline anchor+10. Save its
   complete ledger, including optimistic diagnostics and no-proposal failures.
   Optimistic construction is not a feasible-plan certificate.
2. Only a timely nonempty proposal enters one
   `constructive_charging.complete_topology` call, deadline anchor+55. Its native
   phase/wall caps are at most the remaining window; its existing sequence is
   feasibility plus up to two tangent-objective stages. All movement binaries
   are fixed, original physical rows are inventoried unchanged, and all remaining
   variables are audited continuous. Keep `native_lp_certified=False` and every
   fixed-topology bound scoped; no unrestricted optimum is claimed. All native
   stats, captures, preparation costs and failures are retained.
3. A helper return after anchor+55 cannot qualify. Before anchor+60 independently
   replay a returned plan again on the original full case, check exact movement
   topology, equality with helper replay and exact Fraction bill against helper
   output, then durably save plan and replay. Preserve helper failures even when
   an earlier returned witness is physically valid. No extra solve or repair.
4. Materialize each case receipt, then record elapsed INCLUDING that receipt.
   The master receipt's `accepted_within_offline60` is authoritative: it requires
   a physically checked durable witness and all case materialization<=60 seconds.
   A late but physical artifact stays diagnostic; it is not a timely outcome.

The sole scientific readout is whether this unchanged classical candidate can
construct a small replayable fleet under the relaxed offline windows. Record
vehicles, integrated supply/system cost `ops+a'L+.5*sum(bL²)`, all failures and
per-stage wall/CPU/observed RSS. No-proposal, charging infeasibility, unresolved
native status, late return and extraction/replay failure are distinct evidence,
not global infeasibility or opponent wins.

## Inputs, provenance and outputs

Read/hash once the driver/protocol, October17 case lock, final screen summary,
historical replay-verification report and the two old seed17 graph result/
supervisor context pairs. Validate those compact old receipt digests against the
historical replay audit. Do not reread original raw traces, old model artifacts,
full legacy hash inventories or protected banks. Actual imported `egglab` Python
source closure is narrowly recorded once in-process after import and after each
case, limited to modules from this worktree. Native backend identity/stats come
from the unchanged helper. No source hash is computed during static preparation.

`attempt01/receipt.json` and each case `receipt.json` begin as exclusive incomplete
placeholders. Final reports use exclusive temporary files and atomic replacement
of only their own placeholders. Retain interruption/failure evidence and partial
files; never reuse the namespace. Per-case directories contain construction
ledger, event stream and, only when independently checked, plan/replay. The case
receipt retains the helper's complete stage results/inventory/failures; master
receipts save whole-case timing and validity, total CPU/wall/RSS and consumed
input/source hashes. Whole-process zero exit plus complete master report means
the diagnostic finished; it does not mean both cases were feasible. Inspect
`feasible_cases` and every case receipt separately.

Old graph seed17 bills/vehicle counts provide labelled unmatched historical
context only. They used a learned/pruned policy, different solver seed setting,
search allocation and end-to-end accounting. The relative number is not a
paired advantage, speedup or evidence that this baseline beats learning.
All cases remain reused synthetic development evidence, with shared generator/
physical profiles. Every qualified old source/result and incomplete flag stays
unchanged. Any later comparative experiment needs its own prospective design.
