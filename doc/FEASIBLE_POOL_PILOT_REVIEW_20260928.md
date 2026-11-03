# Feasible-pool pilot implementation review

28 September 2026 UTC. Scoped source/protocol review passed before execution.

The prospective comparison separates a pricing-time reserve from feasible-pool
reuse. The legacy cold arm retains its defaults. Both reserve arms pay for their
own initial solve, and the reuse arm imports only its own eligible predecessor.
All 24 cells remain development data; the public depot variants share a timetable.

Root reviewed the optional core controls and scientific comparison. Default
state identities, result fields and pricing-call ordering remain unchanged.
The reserve changes pricing time allocation inside the existing total limit;
the ordinary next master can process a returned column. The focused fake-clock
test confirms two pricing columns reach that master and improve its mixture
before the reserve prevents a third request. Non-preemptible operations can
still overrun their allowance; the outer child deadline remains authoritative.

The new reuse policy imports only physically replayed complete-fleet columns
from the independently expected predecessor identity. It rebuilds the target
mixture and lower certificate; poisoned old weights and lower bounds are ignored
in the core test. An imported feasible upper without fresh target pricing is
never certified. This first implementation supports a direct state-zero to
state-one transition, not a recursive history of inherited columns.

Luna independently reviewed the runner, protocol and batch wrapper. It confirmed
24-cell accounting, strict on-time complete predecessor admission, timeout
precedence, process-group cleanup before sealing, and the one-CPU/8-GB/two-hour
envelope. During root review, an admission fallback for missing evidence was
removed and tested. Protocol wording was corrected to require reserve telemetry
only on the two reserve arms; the legacy event schema is preserved. Root checked
the final source-hash-list addition and focused-test correction after that review.
The independent review is preserved at
`research-20260928/feasible-pool-pilot/INDEPENDENT_REVIEW.md`.

Validation reported by the implementation agents: 9 new core tests and 96
existing native-hull/compact-wrapper/policy tests passed, plus 8 focused runner
tests. These use fake oracles/fixtures, without new native optimization. Python
compilation, design export, batch shell syntax, source hashing and whitespace
checks passed. Full repository CI remains a separate gate on the published
execution commit. Freeze a clean published checkout before the single new
submission. No computational outcome or public speedup is claimed by this review.
