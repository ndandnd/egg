# First fixed-physics reuse qualification: interpretation

The parent task executed the first and only frozen grid at commit `9c57b45`.
All twelve cells certified, with interval widths approximately 0.000398597,
below the declared 0.01 tolerance. Outputs are preserved in
`physical-reuse-qualification-work/result/reuse_qualification/20260921-attempt1/`.
Independent certificate and runtime review is recorded separately. This note
interprets the observed workload; it is not that independent audit.

| Arm | State 0 calls | Unchanged state calls | Positive tilt calls | Negative tilt calls | Total calls |
|---|---:|---:|---:|---:|---:|
| Cold | 3 | 3 | 3 | 3 | 12 |
| Retained columns | 3 | 1 | 1 | 1 | 6 |
| Retained + analytic proposal | 3 | 2 | 2 | 2 | 9 |

Calls include every seed, clean pricing and analytic proposal. All arms pay for
their own state 0. In later states, retained columns alone already reach the
minimum one complete clean pricing call needed by this certificate. The
analytic proposal adds one call without eliminating the final clean call.
There is consequently no avoidable column-discovery work for a learner on
this fixture after initial qualification.

Every interval contains the independent continuous optimum: 18 in the first
two states and 17.8 in the tilted states. Optimal charging changes from 5/5 to
4/6 to 6/4. The exact marginal price in both charging slots remains 1.3; the
optimal load change cancels the tariff tilt. A solver-selected tangent-master
price need not equal this exact gradient, so these statements do not claim
exact uniqueness or accuracy of the recorded dual-price labels.

The entire grid took about 3.09 seconds. Cells ran in separate subprocesses,
and complete times include interpreter imports and input/output. Fixed ordering
and first-load effects are substantial at this scale. No reproducible speedup
claim follows from the tiny elapsed-time differences; call accounting and
certificate correctness are the useful findings.

The positive-tilt analytic proposal is marked novel by the frozen exact
column-key rule. Independent review found that it differs from an already
retained endpoint by only about 7.1e-15 kWh. It is a numerical near duplicate,
not a useful new physical charging option. The frozen raw key and result were
preserved. A future experiment should predeclare an additional diagnostic
distance for near duplicates without silently changing production column
identity, operating-cost identity, or load reconstruction policy.

This qualifies the fresh-state reuse path under fixed original EVSP physics.
It does not test shared grid capacity, multiple vehicles, hard integer duty
choices, or an operational benchmark. The next workload should introduce
competing fleet structures and additional continuous charging opportunities,
remain seed-free or use newly registered unprotected seeds, and be frozen
before execution. Retained columns must exhibit actual additional discovery
work before a learned proposal is useful to investigate. A failed/slow cell
remains a result and must not be replaced by a more favorable fixture.
