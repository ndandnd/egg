# Offline classical competence: one usable endpoint, one missed endpoint

25 October 2026. The sole frozen attempt finished normally. This is a two-case
development diagnostic, not a matched ML comparison or CF1 controller qualification.

| Case | Greedy proposed buses | Independently replayed and admitted within 60s | End-to-end case time | Integrated supply cost |
|---|---:|---|---:|---:|
| scale:50685:40 | 15 | Yes | 13.1090s | 1856.03542 |
| scale:50605:80 | 29 | No | 64.6127s | Not admitted |

The 40-trip candidate passed separate physical replay and exact objective checks.
The historical graph seed17 endpoint used3 buses; the historical80-trip endpoint
used5. These are unmatched context: solver seeds, allocation, policy and clocks
differ. They show that the greedy constructor is far from the known attainable
fleet counts, not a quantified paired ML advantage or a failure of classical
optimization generally. This is not the GRASP algorithm in the literature.

For80 trips, the charging helper retained an internally feasible candidate but
its final return missed the55s completion cutoff. Its second objective extraction
also recorded `Shared fixed charging deadline exhausted`. The caller consequently
performed no independent replay and admitted no endpoint. This is not evidence
that the topology or instance is infeasible. All internal candidates and failures
remain in the receipt. Receipt publication increased total time from55.3594s to
64.6127s; it cannot be omitted from the attempted60s endpoint. Both cases remain
in the denominator. `passed=true` in the master receipt means the diagnostic
produced complete records; only1/2 cases has an independently admitted witness.

The process used78.45s elapsed and67.64s user+system CPU by `/usr/bin/time`, within
its separate180s/240CPU-second package. Observed peak RSS was1,178,386,432 bytes.
No retries, repairs, additional cases, model inference, full integer search,
cluster access or protected data were used. Native seed stayed the backend
default; its numeric value was not independently exposed.

Nested helper inventories made the complete case receipts40,243,988 and
327,269,509 bytes. They are preserved unchanged locally and losslessly archived
as `receipt.json.gz` alongside compact `summary.json` and the master receipt.
The one metered summary/archive process used3.90s elapsed/3.42CPU seconds. Each
original's streaming SHA256 and archive size are in `summary.json`; no second
full hash audit or numerical execution followed. Repeated inventories and
serialization are real overhead, not solver time to hide.

## Research consequence

Do not launch the192-assignment comparison with this constructor as the strong
classical arm. First replace its myopic fleet construction with a meaningful
classical route/path-cover and charging-aware improvement method, informed by
GRASP and reduced-cost selection. Establish attainable fleet count and charging
feasibility on development cases before freezing a matched comparison. Preserve
this negative result. Separately, stop collecting duplicated full inventories at
each intermediate step in a future version; retain enough independently checkable
physical evidence once and report its actual cost. That source change needs a
new protocol, not retroactive admission of this80-trip outcome.
