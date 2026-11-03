# Integrated launch source review

29 October 2026. Source-only inspection of `worker.py`, `run.py`, `PROTOCOL.md`, `native_probe.py`, `independent_verify.py` and `NATIVE_SOURCE_REVIEW_RESPONSE.md`. Also read the needed source-only `native_recharge` schema/compiler/backend API, `native_pathflow` builder/recovery, empty package initializer and `sistig_native_case.native_case_from_payload`. No imports, tests, compilation, hashes, input-data inspection, solver calls or commits were performed.

## Decision: one preservation blocker; otherwise scoped source pass

The probe repairs address the previous no-optimize, stale OA extraction, negative-interval and export-mapping issues. The planned Q0 is an appropriate narrow runtime gate, not something this review claims has passed. **Before freeze, make the owner preserve the complete six-state assignment when the worker is killed or exits without `results.json`.** The present owner receipt only says result_status=MISSING; it has no Q0/OA/MIQP/ROOT_QP/PRICE_LP/PRICE_MIP rows in that branch. A hard CPU limit, outer wall timeout or abrupt native failure bypasses the worker's ordinary exception/summary code. This conflicts with the protocol's unconditional preservation of all assigned states.

Minimal repair: owner emits a separately labeled administrative fallback with all six assignments whenever the worker result is absent/unreadable. It can use already written current-attempt stage packets/events to distinguish completed/attempted states, or conservatively mark state unknown/unreported without inventing success. Preserve malformed/partial artifacts; do not rerun. Ensure unreadable results cannot prevent the owner receipt and child closure record. No scientific result should be inferred from administrative fallback.

## Source findings

### Q0 and input translation

- Literal Q0 matches the schema field order and physical compiler: one mandatory10kWh service, forced terminal10kWh charge, operations7. OA/MIQP/root share the quadratic convention; linear pricing expects7+.3×10=10. Four specified corruptions target energy omission/excess, movement omission and duplicate allocation.
- Q0 requires OPTIMAL and the expected load/operations/objective, plus independent strict physical replay; failure stops before public construction. It is executed once inside the new worker. There is no retry loop. The continuous root happens to have the same forced physical plan here, so replay is meaningful for this literal case only, not general fractional roots.
- `public_case` reproduces the established source adapter's fields, including terminal_open0/deadline1800, resource policy, depot, movements, fee and stored numerics. No data-supplied filesystem path is followed. The exact two input buffers are pinned/admitted once and only historical route movements are used for the common binary start.

### Cached import closure

The scientific local modules are compared with the committed revision, cached and loaded from those admitted bytes. `egglab.__init__` contains no imports; the inspected builders use the cached recharge/pathflow modules. `recovery_lift` imports occur only in unused solver/completion branches. Native installed packages remain the explicitly version-checked external closure. Owner/worker bootstrap executes before its later byte admission; this is an ordinary disclosed bootstrap trust boundary, not literally execution of every line from cache. The protocol's language should not imply otherwise.

### Objectives, candidates and raw statuses

MIQP and OA represent the same supplied compact graph, all allowed bus counts and quadratic supply objective; the common start is binary topology only, with acceptance UNKNOWN. OA preserves its best evaluated candidate independently of last raw status. Negative OA intervals stop as contradictions. No-optimize returns explicit empty diagnostics rather than extracting unsolved native attributes. Continuous exports include objective/Hessian convention, variable/load indices and solved linear/OA rows; they remain numerical ingredients, not ideal-model certificates.

The worker selects the lowest evaluated OA/MIQP candidate, with OA winning ties by append order. It does not require strict replay success before selecting the diagnostic gradient; the protocol explicitly permits an unqualified point for diagnosis. This must stay visible: neither the selected floating value nor its gradient becomes a physical optimum/support certificate. The independent replayer records exact reconstructed costs separately. LP is cold; MIP uses the selected topology only. Native infeasibility or replay failure must not be interpreted as physical topology infeasibility.

### Independent replay

The verifier imports only stdlib and reconstructs service coverage, movement chronology, intervals, serial charger sessions, SOC, terminal refill, conservation and costs from supplied case fields. It preserves raw energy allocations without repair. Representation-only load/ops/SOC mismatches are separated from physical violations, so `physical_strict_pass` is intentionally weaker than `strict_pass`. Any admitted physical upper must use its reconstructed `objective_exact`, not the raw candidate's float load/ops cost. The verifier is scoped to at most one shared connector, matching this case and Q0; it is not a general multi-connector verifier.

### Funding, timing and states

Stage funding reserves120CPU/180wall beyond the next complete nominal allowance. Worker hardCPU1700, observed worker threshold1740, wall2200 and owner2397 alarm sit within the NEW1800CPU/2400wall package. Native time limits are advisory, one thread is configured, and final owner self+waited usage avoids child double counting. RSS is observed peak process usage, not continuous aggregate containment. The outer time meter remains authoritative through publication/exit.

Ordinary caught failures retain the active FAILED row and pad unattempted assignments; missing price candidates pad both price states. A stage's DELIVERED label describes delivery of a diagnostic packet, not native optimality, physical feasibility or timely success under every clock; native fields and replay must be interpreted separately. The abnormal-worker preservation blocker above is the missing closure path.

## Scope of approval after repair

Subject to that administrative preservation fix and an actual frozen source/launch record, this review supports one prospective diagnostic attempt with mandatory Q0 runtime qualification. It does not establish Q0 backend behavior, source/input pins, numerical feasibility, resource compliance, exact support or public scientific success. Those require the future single paid execution and its complete outcomes.

## Follow-up: owner preservation and timing patch

Inspected only the changed owner fallback block and worker stage-clock block. Missing/killed-worker outcomes now preserve all six assignments through an administrative ledger; durable packet timing is explicitly prepublication, and complete serialized stage duration is retained in the master. This addresses the central missing-ledger path and the timing distinction.

Three small malformed-report paths still need closure before the blocker is fully resolved: validate master top-level `status` and each assigned row's `status` before later receipt/ledger access; reject non-dict event JSON before calling `.get` (a scalar/list currently raises uncaught AttributeError); and require a valid master result for owner success rather than allowing child exit0 plus absent/malformed results to return0. These are defensive administrative checks, not reasons for any scientific rerun. No execution was performed.
