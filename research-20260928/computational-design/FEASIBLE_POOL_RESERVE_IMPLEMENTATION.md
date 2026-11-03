# Opt-in feasible-pool reuse and pricing reserve

The native hull coordinator and compact path-flow wrapper now accept
`reuse_policy="feasible_pool"` and `pricing_reserve_seconds=10.0`. Defaults remain
`"certified_only"` and zero; their state identities, serialized result shape,
strict predecessor status check and pricing call ordering are unchanged. An
opt-in identity records the policy and reserve without adding fields to
`Budget` or changing its existing serialization.

An external runner must first establish an on-time, complete predecessor
receipt and independently derive its expected state identity. The core then
accepts certified, budget-exhausted, stalled-bounded or bounded predecessors
only in feasible-pool mode. It requires matching state, physical, pricing-oracle
and extraction-policy identities; every unique imported complete-fleet column
is physically replayed and must originate from that exact predecessor state.
This first mode is intended for a direct state-zero to state-one transition,
not recursive import of columns from older ancestors.

Only columns cross markets. The new state constructs a feasible one-column
mixture under its own market, then runs its own master and pricing. Old mixture
weights, prices, lower certificates and status never cross. Without a fresh
target-market pricing certificate, a preserved feasible upper can be reported
but certification cannot occur. The pricing reserve checks remaining time
before each call and caps that call's native wall allowance to remaining time
minus the reserve; the total wall budget is unchanged. A native call can still
overshoot its own target. Explicit pricing-request allowance and reserve-stop
events, plus distinct call-cap and reserve reasons, preserve that accounting.

Focused fake-oracle tests cover unchanged default hashes, bound-only import,
poisoned old weights/lower, provenance/control mismatches, reserve stop and
absence of a fresh target lower. No native MIP or new qualification run was
started. The prospective pilot must separately compare cold and reuse arms at
matched markets, quality and full state-zero-plus-state-one time.
