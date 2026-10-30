# Prospective Sistig flat-price native pricing pilot

27 September 2026. **Design only:** no optimizer was run, no cluster job was
submitted, and this document does not authorize or implement an execution.
The pilot has exactly two independent cells: the unchanged full 37-service
Hildenbrand input restricted to source depot 15, and the same full input
restricted to source depot 16. It uses the compact path-flow formulation. The
source two-depot problem is not represented by either cell or by their union.

## Admission gate and question

This is one bounded price-oracle intake test: can the compact complete-fleet
pricing model return a replay-valid incumbent and a solver-conditioned global
lower bound for each fixed public timetable graph at one explicitly synthetic
flat price? It is not a hull computation, planner run, tariff sweep, fleet-size
study, operational calibration, or test of the publisher's schedule.

The twenty-control compact path-flow qualification is a hard prerequisite.
The completed first attempt at `ebb146e9de01d0c6aa13b03eb2348337a1d0b3f0`
has 20/20 admitted controls (16 numerical certificates and four expected
infeasibilities). Its independent audit passed and rejected 25 corruptions.
The future run freeze must explicitly reference the gate evidence by exact
path and hash: `result/native_pathflow/20260927-attempt1/summary.json`
(SHA-256 `4b980b32cce6bda057c2f727d7a4ecc3b379e54cfd4a41214487c33408578f03`),
`result/native_pathflow/20260927-attempt1/MANIFEST.json` (SHA-256
`2ab225a5b79cf278c5ef55c834ba835a65126f09f370b9b967e5fac8a2f5327d`), and
`result/native_pathflow/20260927-attempt1/review/audit-report.json` (SHA-256
`560caf8d0e48789a7b76749f6ba422d64a118d30a38edd79e84a9074db6a4de8`;
review-package manifest SHA-256
`ebb85951b4a422f282933d9cdbc99a44ce7a957d191ece4dd58e9cf22fd354dd`). The
public pilot's own source preflight and immutable freeze remain separate
requirements. Any failed gate control, missing raw evidence, or incomplete
independent review leaves this pilot inadmissible; do not adjust that gate
from this pilot.

## Frozen public cases and objective

Read `data/public/sistig_26088190_v1/hildenbrand_native_cases.json` and
regenerate both cases with the checksum-pinned public adapter. Require the
recorded and recomputed `NativeCase.identity()` values to match exactly:

| Source depot | Case identity | Services | Direct / depot / pullout / pullin modes |
|---:|---|---:|---:|
| 15 | `1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7` | 37 | 666 / 630 / 37 / 37 |
| 16 | `216693551f2e58ec8aab3cba68352656ec99bab8db13c671edd028542acfeb3d` | 37 | 666 / 595 / 37 / 37 |

The full directed movement graph, all source times and legs, service records,
modeled energies, 400 kWh usable inventory, zero additional reserve, unit
efficiency, one 360 kW connector, 30:00 return/recharge deadline, 37-bus cap,
hourly market edges and synthetic `f100` used-bus cost remain unchanged. The
input preserves its exact half-minute timestamps. Do not drop modes, join the
depots, round times, change energy, alter the case-selection policy, or use
historical vehicle labels. The original source archive and publisher-generated
schedules are not solver inputs.

The reviewed derived-input anchor is SHA-256
`af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6` for
`hildenbrand_native_cases.json`. The current compact formulation/review
snapshot is SHA-256 `45864e08bffb81dc29b27774449f944fd074cb6654a593ab0d482abdad935c7d`
for `native_pathflow.py` and `28b9f8cdfbfbd6fca21d75419aeaf61548bf34ad5cc5c22cdcc86b9c8fd5b22a`
for `NATIVE_PATHFLOW_PREFLIGHT_REVIEW_20260927.md`; the native physical module
reviewed with it is `0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3`.
These identify the current reviewed candidate, not an execution freeze. The
future manifest must record the actual final commit and all final file hashes;
the compact formulation and physical dependencies must match the independently
passed gate exactly.

For each case, make one **cold** complete-fleet pricing call at the uniform
price vector `(0.2, ..., 0.2)` with 30 entries, one per hourly market period
from 00:00 through 30:00. Price and objective units are explicitly synthetic:

`min_x [100 * used_buses(x) + 0.2 * sum_t grid_kWh_t(x)]`.

The configured deadhead-time cost remains zero. The coefficient 0.2 is in
synthetic objective units per grid kWh; it is not a market tariff. This query
has no quadratic supply term. Each query gets a fresh model/process, no warm
start, no seeded historical or constructive schedule, no imported pool, and
exactly one native pricing optimization.
Do not add a second call, price perturbation, hull master, planner run or
reoptimization if a cell is weak or fails.

## Predeclared feasible-reference cross-check

The source-derived, replay-checked one-trip-per-bus witness is an external
feasibility cross-check only, not an initial solution, fleet recommendation,
optimality claim or lower bound. Under the frozen lossless case and flat price,
its 37 buses cost 3,700 synthetic units; adding 0.2 times its modeled grid
energy gives approximate feasible objective upper references of 4,117.9753
for depot 15 and 4,253.9629 for depot 16. These are computed from the JSON's
2,089.8764409985943 and 2,769.8144794193886 kWh witness totals. Before use,
the later independent audit must replay each witness under the frozen case and
recompute its objective. Never label these values optima or use them as solver
starts.

Report the native solver's replayed-incumbent upper and admitted global lower
bound separately from the witness values. The witness is a further valid
feasible upper cross-check; if independently revalidated, the tighter of it
and the native replayed upper may be shown as an auxiliary enclosure, without
replacing either raw result. A native lower bound exceeding the validated
witness objective beyond the existing guard is an identity, objective,
solver-bound or replay discrepancy; retain the evidence and fail closed.

## Fixed execution envelope

Use explicit Gurobi (`GRB`) with one solver thread and no backend fallback.
For each cell, fix one native phase to at most 180 seconds, one complete
pricing routine to at most 240 seconds, and an external child timeout of 255
seconds. The 240-second deadline covers the scientific pricing routine and
physical replay/admission; the worker checks it before writing its result. A
late result and its raw evidence are preserved but fail admission. The
255-second hard child limit also covers final result serialization and is a
kill margin, not extra scientific compute budget. The batch wrapper's 560-second
timeout is also only a hard stop within the 12-minute allocation. Keep the
qualified bound-admission, roundoff normalization, serial-decoding and physical
replay policies unchanged. Do not alter tolerances or retry a timeout/status.

With the admitted 20-control gate passed, the entire two-cell attempt may use at
most one sequential Slurm job: one CPU, 8 GB RAM, 12 minutes wall time, with
`scaglione-compute-01` explicitly excluded and requeue disabled. It is not a
job array and the two cells must not run concurrently. A later execution still
requires the live resource-policy/queue checks and a distinct frozen source
commit. No job has been submitted.

## Immutable input and evidence requirements

Before a future launch, the root-owned runner must create a new, exclusive
attempt directory and freeze the actual source commit, environment and SHA-256
of the complete dependency set, including at minimum the public derived JSON,
public extractor, `native_recharge.py`, `native_pathflow.py`, pilot runner,
qualification protocol/test, and independent compact-gate review. The freeze
must contain the complete serialized `NativeCase` payload for both cells—not
just case names or hashes—plus all 30 price entries, full graph and resource
rows, case identities, objective, backend, limits and environment. Record the
versioned Figshare DOI and CC BY 4.0 attribution. Also preserve the exact
manifested witness input used for the upper cross-check. If any hash, case
identity, source count or configuration changes, do not launch under this
protocol; make a new protocol and freeze first.

Preserve, without pruning or overwriting, for **both cells including every
failure**:

- frozen and per-cell full input payloads, source/dependency hashes, command,
  worker launch, environment, backend/library identity and limits;
- every native phase start/status, solver status, bound, incumbent objective,
  gap and wall time, full pre-decoding raw variable values and index/name/type
  mapping, incumbent extraction, normalization/correction ledger, movement
  selections, reconstructed paths, sessions, market loads and replay events;
- both objective reconstructions, lower/upper calculations and the witness
  replay/objective cross-check;
- stdout, stderr, exceptions/tracebacks, partial valid trace prefixes,
  per-worker and supervisor receipts, return codes, timeout state and complete
  Slurm job/node/exit/elapsed/MaxRSS records.

Write explicit null/missing statuses when no incumbent or raw value exists.
Record and attempt the second independent cell even if the first fails. Never
replace a first attempt or retry within this protocol. A job disappearing
from the queue is not evidence of completion.

The future attempt destination is
`result/sistig_pricing/20260927-grb-job${SLURM_JOB_ID}-attempt1/`, matching the
batch wrapper; it must be created exclusively. Keep the complete local archive
unchanged, including all stdout/stderr and full solver-license details. A
public copy may omit only a separately verified sensitive license stdout file.
Omit that file as a whole and include a manifest with its relative path, byte
length, SHA-256 of the full local original, and reason. Keep the complete
original locally. Copy all numerical results, full inputs, event traces, raw
solver variables, receipts, exceptions, and every non-sensitive log
byte-identically to the public evidence package; do not redact or rewrite
numerical/input/event files. Include the CC BY 4.0 attribution and versioned
Figshare DOI. No private GIRO material belongs in this public-data package.

## Outcome interpretation

For each cell, retain the exact returned status. An independently audited
`certified` interval at the existing `1e-4` width is a certified result only
for that solver call, input identity and numerical policy. A `bounded` result
with a finite admitted lower bound and independently replayed feasible upper
is an acceptable **bounded pilot outcome**; report its full interval and width,
not as an optimum. A wide interval is not silently promoted by the external
witness. `unresolved`, timeout, exception, incomplete accounting or missing
incumbent remains unresolved. `infeasible` conflicts with the already replayed
full-service witness and must be retained as a failure for independent
diagnosis. None of these statuses permits an unrecorded rerun.

The global lower bound is conditional Gurobi evidence under the qualified
numerical admission rule, not exact arithmetic. A feasible upper requires
successful independent physical replay. The 37-bus reference can check/tighten
the reported feasible upper after replay; it does not imply that 37 buses are
needed or that a solver found an optimum. Even two valid price responses at
one synthetic flat price do not establish a convex hull, price support,
market-scale effect, real cost, operational fleet plan or general claim.

## Status

This is a prospective protocol only. The root-owned runner and five pure tests
are reported complete; its independent source preflight and final execution
freeze remain pending. The compact twenty-control gate and its independent
audit have passed as cited above. No optimizer, cluster or publisher code has
been run for this pilot, and no pilot artifact exists yet.
