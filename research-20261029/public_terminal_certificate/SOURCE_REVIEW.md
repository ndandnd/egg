# Exact terminal witness: source-only launch review

29 October 2026. Read `construct.py`, `worker.py`, `run.py`, `PROTOCOL.md`, `LAUNCH.json` and the already inspected behavior of `independent_verify.py`. No input data, candidate packets, execution, imports, tests, hashes, native calls or commits were used in this review.

## Decision: scoped source PASS, pending freeze and runtime controls

No material defect found in the declared terminal-only construction/admission path. This supports freezing one new attempt after recording its actual source revision and FROZEN launch status. `LAUNCH.json` is currently DRAFT/null revision, so the owner correctly refuses launch in the state reviewed. This review is not a successful construction, exact upper certificate or resource receipt.

## Construction preserves the intended scope

The input candidate is not mutated. Selected movement IDs retain their original order; every original allocation cell is converted to an exact rational and retained. Initial validation rejects duplicate cells, negative energy, positive unselected/out-of-window energy and an original shared-capacity excess. Those are outside the stated terminal-only scope rather than silently corrected.

Route recovery verifies full service coverage, incoming/outgoing uniqueness, path cardinality and no disconnected/repeated components. Selected leg endpoints and times are checked. The sequential SOC calculation excludes original terminal charging, retains all depot charging, and rejects every nonterminal reserve/headroom violation. The per-bus required terminal grid amount is therefore exactly `(B−terminal_arrival_soc)/eta` under the admitted full-start, loss/consumption rules.

Surpluses are removed for every bus before any deficit addition, in latest-interval order. Removal changes only that bus's terminal allocations and releases shared capacity globally. Deficits are then added in deterministic recovered-route order to the latest eligible exact shared spare. Existing cells are reused; new eligible terminal cells are explicitly appended. Additions never exceed the computed interval capacity. Failure stops without a new allocation policy or topology search.

Greedy failure must remain exactly what its error says: inability of this fixed latest-first procedure to complete the witness, not proof that no terminal allocation or route is feasible. The program makes no completeness claim for the heuristic. Even if a more general resource pattern made greedy order important, mandatory final replay prevents false admission of a successful-looking invalid witness.

Every recorded changed cell is asserted to be a selected pull-in allocation; nonterminal cells cannot change. Original reported load/SOC/ops fields are deliberately dropped so they cannot contaminate new-witness admission. Exact per-bus conservation is checked before returning.

## Independent replay and upper-bound meaning

The worker calls the separately authored verifier on the newly constructed candidate and requires `strict_pass`, not only its weaker physical flag. The verifier reconstructs paths, original windows/resource intervals, serial shared-connector charging, chronological inventories, full terminal inventory and exact operations/market objective. Fractions are accepted directly; no float round trip is introduced into physical admission. The published exact upper is `audit['objective_exact']`, not an old native objective or a sum of stale reported loads.

The constructor's whole-gap SOC check is justified by no parked auxiliary draw, no taper and monotone depot charging. The independent serial allocation supplies concrete within-window timing. Multiple connectors or altered physics are not being inferred here. Failure of this new replay is preserved and prevents an upper claim.

## Prospective controls

The two literal original terminal quantities10±1/1024 are within the20kWh one-hour capacity. Their targets are exactly10; both surplus removal and deficit filling are exercised. New strict replay plus total-grid10 checks the repaired quantities. Subsequent removal of1kWh must fail physical replay; a zero-power deficit must raise instead of returning a witness. These controls occur once before the public state. They do not qualify every possible multi-bus greedy pattern, but final independent replay remains the soundness gate for the public construction.

No control has run as part of this source review.

## Physical fleet-count bound

The claimed bound for every physical fleet using at least3 buses is valid under the frozen fee, market and admitted nonnegative-input assumptions:

    cost ≥ 3*fee + a_min*service_energy/eta.

Full initial/terminal inventory implies grid energy equals total service-plus-movement consumption divided by eta. Movement consumption and monetary movement costs are nonnegative; each market linear coefficient is the frozen binary .2 and quadratic cost is nonnegative. The worker uses exact Fractions for each input and computes that expression. Its comparison to the new exact upper is strict, as required to exclude3+ physical minimizers.

This does not exclude higher-cardinality components from a hull mixture, prove an exact two-bus optimum, certify any fixed-price response or settle support. The protocol/result scope correctly says physical fleet-count exclusion only. A display float is ancillary to the exact comparison.

## Input/source ownership and preservation

The only scientific input paths are the source-defined current-campaign descriptor and MIQP packet from exact revision `253c1e29295e766b3889fc8f5c28d9808e00b3d6`. Their whole JSON is transiently decoded as authorized; only descriptor and MIQP.result.candidate enter the new construction. No input-supplied path or executable content is followed. Each buffer is read/admitted/hashed in the future metered worker, not in this review. Local construct/verifier functions execute from the compared cached source bytes. Their imports are stdlib only; `-I -S -B` avoids application/native solver imports.

Both literal/public states survive ordinary worker failure through the summary. The owner validates a complete two-state ledger; absent or malformed worker results give UNKNOWN_UNREPORTED administrative states and do not return success. It kills the owned process group and waits on timeout, preserving an unresolved-child marker if needed. No retry is present. The source/launch admission is still prospective; no actual pin or source commit is certified by reading these strings.

## Funding and timing

The reviewed limits match NEW50CPU/90wall: worker CPU hard40, observed worker target45, outer wait60, owner alarm87 plus cleanup3, owner CPU soft5/hard50. The final external meter includes bootstrap/admission, construction, replay, publication and parent/waited usage once. Worker/owner snapshots are prepublication; they cannot replace the final meter or prove instantaneous aggregate RSS containment. A hard stop can lose scientific results but the owner retains administrative assignment states. Actual compliance awaits the single future attempt and final receipt; reviewer CPU is UNKNOWN.
