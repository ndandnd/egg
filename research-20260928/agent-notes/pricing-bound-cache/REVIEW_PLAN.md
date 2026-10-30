# Review plan: opt-in price-indexed physical-bound cache

A saved physical pricing lower is reusable across supply markets only when the physical feasible set, cost, load mapping, oracle, extraction policy, and posted price vector are unchanged. For that exact key, a numerically qualified lower bound `L(p) <= inf_x {c(x) + p·L(x)}` can be converted for a new supply cost `F_new` into `L(p) - F_new*(p)`. The conjugate must be recomputed from the target market's frozen stored numbers and rounded outward. The original posted vector `p` stays attached to the cached physical bound; this conversion does not present `p` as the target mixture's marginal price or as a current target solver output. The old market's hull lower certificate cannot simply be relabeled.

## Cache-record invariants

- In-memory entries must bind to the frozen physical-case identity, exact serialized price vector (no tolerance-based price matching), pricing-oracle/formulation identity, extraction policy, and an evidence/source-state digest. The runner/archive layer should pin the source attempt, manifest and matching raw pricing-result event; do not require archive paths or a particular archive format inside a generic solver API.
- Cache only a finite **lower** bound for the physical linear-price problem, with original solver status, backend/stats, lower/upper result, tolerance guard, and time/config provenance. Never promote an incumbent or a pricing upper bound to a lower bound.
- Identity/provenance establishes which computation produced the number; it does not prove the solver's lower bound. Keep its native numerical/tolerance qualification explicit, including when the source solver reported `OPTIMAL`.
- With no cache configured, preserve the unchanged cold path. If an entry is explicitly supplied but its physical inputs, price vector, oracle/formulation, extraction policy, evidence digest, bounds, status, or evidence do not validate, fail closed and record the rejection; never silently fall back to cold behavior. Reject malformed, nonfinite or reversed bounds, unsupported statuses, and incomplete/mismatched pricing records.

## Target-market certificate gate

- Mark the target state and market identity separately from the cached source. For every use, compute `F_target*(p)` anew from that target's coefficients, verify its finite domain, and outward-round `L(p) - F_target*(p)` downward. A target certificate should retain the cache-source identity and target-market identity together.
- Cached re-evaluation may strengthen the target state's best valid global lower, but a cache hit alone must never permit `certified`. Require at least one successful **fresh target-state physical pricing solve** under the current target state before certification; it must return a complete plan and a valid current-state pricing lower, with matching case, oracle, extraction, and price identities. The cached original `p` remains provenance for its own conjugate conversion and must not be relabeled as the fresh target solve's price. Certification still requires a replayed feasible target-market mixture and a fresh global enclosure within the frozen epsilon.
- Do not transfer old-market conjugates, hull lower values, restricted-pool gaps, mixture weights, duals, or prices as target evidence. Feasible-plan reuse, if separately enabled, must replay plans and rebuild the target master independently.

## Focused reviewer checks

1. Positive fixture: same physical identity/oracle/policy and bit-identical `p`; match exactly one sealed pricing result; verify the cached numerical lower and recompute target conjugate independently with exact rationals of stored inputs.
2. Gate fixture: a valid cache bound plus a tight feasible upper, without a fresh target pricing solve, remains un-certified. Add a fresh matching target solve and verify certification is possible only after the fresh target lower and target mixture replay pass the normal epsilon rule. An explicitly supplied invalid cache must fail closed with a recorded error; absence of a cache retains the old cold path.
3. Negative fixtures: one-bit price change; physical identity, oracle, extraction, backend/schema or source-pin mismatch; absent/duplicate event; nonfinite or reversed bound; invalid target conjugate domain. None may create a target certificate.
4. Preserve target lower provenance if several old-price bounds are reused: each re-evaluated conjugate must use the target market and the reported best lower must be the maximum of individually valid outward bounds. Keep target solve counters/timing distinct from cached lookup/re-evaluation cost.
5. Verify the default cold/certified-only path is unchanged and no cache import reduces native call requirements or relaxes the strict target freshness gate.

The 28 September posthoc diagnostic is a mathematical lead, not proof of cache correctness: its source `pricing_lower` inherits a native solver tolerance qualification. The proposed cache therefore needs both provenance and the fresh-target certification gate; neither replaces the numerical lower-bound evidence.
