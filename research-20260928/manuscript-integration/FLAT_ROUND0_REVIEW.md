# Independent narrow review: archived flat-price round 0

**Finding: PASS for the qualified archival reconciliation.** The existing
attempt-2 round-0 result supports a tolerance-qualified *native numerical*
flat-price optimum of approximately 408.533136 for the declared depot-15
complete fleet case. It does not establish the exact ideal stored-input
optimum, pass the nonlinear hull protocol, or create a new prospective
flat-price experiment.

I reran the read-only `check_flat_round0.py` and reproduced every field of
`FLAT_ROUND0_SUMMARY.json`, including the three input hashes. I independently
checked the two stored case dictionaries and identities, the 30 prices at
0.2, and the one affine round-0 tangent `(slope=0.2, intercept=0)` in every
period. In the source-pinned `native_recharge.attach_objective`, the tangent
mode minimizes operating cost plus one epigraph variable per period, each
bounded below by that affine load expression. Eliminating the epigraphs
therefore gives the flat linear fleet objective. This identifies the round-0
MIP objective; its separate `true_cost` reconstruction, about 552.358896,
evaluates the quadratic supply function and is not the flat optimum.

I checked the two source commits `282e00b80b6fd9457006429b089269b2a9e2be92`
and `e23a653dcd77b6ce02eb0af5e544fea7edab9eca`. The freeze's hashes
for both `native_recharge.py` and `native_pathflow.py` match the corresponding
Git blobs. Of their common frozen sources, only `native_pathflow.py` differs.
Its builder retains service cover, path, SOC, movement, charging-resource,
load and operating-cost rows and adds two aggregate energy-band inequalities.
The derivation in `doc/NATIVE_PATHFLOW_ENERGY_BAND_DESIGN_20260927.md` proves
those rows valid for intended physical conservation and redundant for integer
points of the old exact normalized stored matrix. The later source also
changes incumbent extraction and replay accounting. The native matrices and
floating tolerance behavior are consequently not asserted to be identical;
the intended complete physical feasible set and flat objective coincide.

The archived round-0 native status is `OPTIMAL`, with incumbent
408.53313588387846, lower bound 408.53313588387834, and 94.933847 seconds
against that call's 180-second cap. The independent
`research-20260927/agent-notes/nonlinear-v2-result-review/REVIEW.md` accepts
the attempt-2 numerical matrix and physical-plan reconstruction while
retaining **FAIL** for the overall protocol: later hull polishing exceeded
its cumulative cap. Thus the round-0 flat solve may be described as a
retrospectively recognized native numerical result, with solver tolerances,
without promoting the failed nonlinear campaign or implying a runtime
comparison.

The exact ideal flat-cost enclosure from
`doc/SISTIG_EXACT_PUBLIC_WITNESS_ADMISSION_20260927.md` remains
approximately `[404.924239883878, 408.533135883878]`. Numerical closeness
of the native optimum to its feasible upper endpoint does not prove exact
ideal equality, because the native lower bound is solver-conditioned and its
stored matrix/tolerances differ from the ideal rational model. No correction
to the reconciliation is required within this scope. This review inspected
only the compact archival metadata, the named source diff and design proof,
and the existing attempt-2 numerical review; it did not inspect raw variable
dumps or run an optimizer.
