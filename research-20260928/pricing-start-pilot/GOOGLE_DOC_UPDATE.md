## Fixed-price starting-point pilot launched — 28 September 2026

Unicorn job 577225 was submitted once at 15:28 UTC and was pending for priority at the launch observation. It requests one CPU, 8 GB and one hour, with one native/numerical thread and no retry or requeue. The published runner passed the complete existing CI gate and independent static review. All four source pools passed physical replay; the eight selected fleet/price queries were frozen before submission, including the observed solver seed and library identity.

The comparison uses the same physical model, query prices and time limits for
cold solving and solving with a checked feasible fleet as a starting hint.
Both arms retain the same known feasible-plan baseline when we assess quality.
The 16 calls cover four development cases and two predetermined price queries;
the two public depots share one timetable. Call order is counterbalanced.

The runner preserves unresolved and failed calls, preparation and native solver
time, and the cost of producing the historical source fleets. A submitted hint
is not an accepted incumbent or an optimality certificate. This is a diagnostic
of the physical-pricing bottleneck; it does not establish a speedup for the full
iterative method or a benefit from learning. Results will be reviewed after the
job finishes and its evidence is sealed.

[Reviewed runner](https://github.com/ndandnd/egg/blob/6759daa4eaeb92152607a3d60840d52988093973/src/experiments/pricing_start_pilot.py) · [Prospective protocol](https://github.com/ndandnd/egg/blob/6759daa4eaeb92152607a3d60840d52988093973/doc/PRICING_START_PILOT_PROTOCOL_20260928.md) · [Independent review](https://github.com/ndandnd/egg/blob/6759daa4eaeb92152607a3d60840d52988093973/research-20260928/agent-notes/pricing-start-runner-review/REVIEW.md) · [Source CI](https://github.com/ndandnd/egg/actions/runs/36443216684).
