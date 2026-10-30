# A checked fleet as a physical-pricing starting point

The latest comparison identified physical pricing as the main measured cost.
The next baseline asks whether an already known feasible fleet helps the native
solver find a good incumbent or improve its bound within the same time budget.
Retaining a fleet in the restricted master does not automatically provide this
native solver hint.

This package develops an opt-in mapping from a physically checked complete fleet
to all compact movement-selection binaries. Charging and battery levels remain
continuous decisions for the solver. Source identity, path coverage, provenance
and physical feasibility are checked; invalid inputs must fail explicitly.
Hint submission is distinct from native acceptance, and neither is a certificate.
Existing defaults and certification rules remain intact.

The [prospective pilot protocol](../../doc/PRICING_START_PILOT_PROTOCOL_20260928.md)
declares 16 fixed-price calls with matched caps and counterbalanced order.
Both arms have the same known feasible-plan baseline when comparing quality.
The [source inventory](SOURCE_INVENTORY.json) identifies the four historical
state-0 pools and their original generation times. It is metadata only;
the execution runner must still check and freeze the exact selected inputs.

The core passed 40 focused pure tests. One bounded CBC check on the cyclic
synthetic case returned a certified numerical interval around 37 within a
5-second call cap (3-second native phase). Its total wall time was about 0.23s;
this is a functional check, not a performance comparison. It preceded the final
pure-tested guard against unexpected integer variables; no second native probe
was run. Solver acceptance of the hint is recorded as unknown. See the
[implementation note](../agent-notes/pricing-start/IMPLEMENTATION.md) and
[smoke receipt](../agent-notes/pricing-start/SMOKE_RECEIPT.json). The independent
[code and protocol review](../agent-notes/pricing-start-review/REVIEW.md) passed.
[Full CI passed](CI_RECEIPT.md) on its first attempt. The original Google Doc
received the [consolidated update](GOOGLE_DOC_UPDATE.md) once; its
[receipt](../agent-notes/google-doc-pricing-start/RECEIPT.md) records the
post-reload persistence check.

No cluster pilot has been launched. Next: build the bounded runner against this
protocol, freeze source and inputs, pass relevant checks, and submit the single
serial job. Its prospective ceiling is one CPU, 8 GB and one hour with one native
thread, no retry/requeue and all failures retained. The diagnostic can justify
testing starts inside iterative solving; it establishes no whole-hull speedup,
scalability or learning result.
