# Prospective exact half-minute source-time qualification

27 September 2026. Protocol `native-halfminute-qualification-20260927-v1`.
No native execution is admitted until source/test/protocol freeze and independent
preflight review. This is a numerical extension gate, not an operational study.

## Scope and numerical policy

The public Sistig Hildenbrand timetable has directed deadhead durations on a
30-second lattice. Preserve them exactly in minute units. Native case source
timestamps now accept nonnegative integers or finite floats that are exact
multiples of 0.5 minutes, with no rounding or tolerance. The horizon ceiling is
2^20 minutes; IEEE double spacing there is approximately 2.33e-10 minutes,
well below the existing 1e-7-minute replay tolerance. This numerical scope is
explicit and comfortably contains the planned 30-hour case; it is not a claim
about arbitrarily large real-valued timestamps. Input counts, indices, vehicle
IDs, depot splits and connector counts remain strict integers, excluding bool.

Integer input values remain integers, with all 15 previously frozen control
JSON objects and case identities unchanged. No schema field is added. Charging
sessions remain continuous; only exogenous trip/leg/resource/market timestamps
must lie on the declared source lattice. The existing single-connector,
constant-power, zero-switching, efficiency and full-replenishment assumptions,
raw-variable recording, 1e-8-kWh conversion budget and admission checks remain.

## Complete predefined gate

Run the original 15 controls followed by the following four controls, always
preserving every result or exception. Original targets/budgets do not change.

| New control | Exact analytical target or status | Reason |
|---|---:|---|
| Half-time multileg | 36 | Halve every original multileg timestamp; double kW and driving-cost/min. All energy and cost terms remain unchanged, with 2.5-minute legs. |
| Half-minute capacity | 7.5 | One bus costs 7 and consumes 0.5 kWh. Its only return window is [0.5,1] minutes at 60 kW, exactly 0.5 kWh; unit energy price. |
| Half-minute capacity failure | Infeasible | Same problem at 59 kW supplies 59/120 kWh, strictly below 0.5. |
| Fractional coincidence | 9 | One bus costs 7, serves A during [0,0.5] consuming 1 kWh, recharges [0.5,1.5] at 60 kW, then an instantaneous outbound leg consumes 1 kWh at 1.5; service B ends at 2 and [2,2.5] at 120 kW restores the full 1-kWh inventory. |

The coincidence graph has one available bus and no direct A–B mode. Charging
completion must precede the coincident outbound consumption; there is no hidden
extra starting battery. All four prices are 1 in every market period. The fixed
19-cell gate therefore expects 15 numerical certificates and four infeasibilities.

## Execution and evidence

Use a separate exclusive attempt root and the actual published Git freeze label:

```sh
PYTHONPATH=src python -m experiments.native_halfminute_qualification \
  --output result/native_halfminute/20260927-attempt1 \
  --freeze-label ACTUAL_PUBLISHED_COMMIT --backend CBC
```

The controller copies the already qualified V2 attempt-preserving process
structure, with its own source hashes, protocol and worker module. One thread;
10 seconds per native phase, 45 seconds routine budget, 60 seconds hard child
timeout, at most 48 planner rounds, certificate tolerance 1e-4, analytical-target
agreement 2e-4. Maximum controller worker allowance is 19×60 seconds; no retries,
parameter tuning or removal of failed cells inside an attempt. Preserve native
status, raw variables, normalization/decoding ledger, witness, target assessment,
stdout/stderr and attempted/returned call counts. New source changes require a
new version/freeze/output directory.

Before execution, run all native and half-minute pure tests with native solver
imports blocked. Independent preflight checks exact validation, integer control
identities, negative controls and the time-scaling argument. After execution,
independently reconstruct the new analytical optima, raw model feasibility and
actual replay, verify the original-control consistency, and manifest the raw
attempt before further use. Passing this gate admits half-minute source times;
it does not by itself admit public-timetable or convex-hull scientific results.
