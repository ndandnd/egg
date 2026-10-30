# Proposed disposition of the failed preflight

**Status: proposed, not authorized or submitted.** The frozen comparison protocol
says: “No retry, requeue, substitute case or seed sweep is allowed.” The failed
job therefore cannot be replaced automatically under that protocol.

Recommended decision: permit exactly one separately recorded replacement
allocation after the minimal preflight repair passes review and full CI. Keep
all scientific choices unchanged: five synthetic development cases plus
Eberbach105, two source markets, four target initialization methods, target
planner and own-price response. Retain the failed job 584876 and every spent-time
receipt permanently. Do not relabel it as a successful or completed comparison.

The replacement would request one CPU, 8 GB and at most two hours on Unicorn,
serial execution with one native thread, no requeue, excluded reserved node.
The 48 child limits, 6900-second controller limit and 7100-second outer limit stay
unchanged. No further replacement or expanded sweep is included. This exception
would cover only the login/compute environment preflight failure, which occurred
before any algorithm outcome existed; it does not authorize result-based retries.

Use a new isolated checkout, leave the failed checkout frozen at 68cfa64, and
create a fresh exclusive launch intent. The prospective freeze must exactly
match the failed attempt’s scientific design fields: protocol, cases (including
physical/market identities, budgets and stage order), hull_controls,
controller_cap_seconds, supervisor_cap_seconds, children_declared,
development_only and rng. The canonical JSON SHA-256 of those fields is
`dc9ca0df332650f48dc4bb4ba1905dc80103847ce6c7202f239b494f91851abd`.
Source/software identities are frozen separately at the reviewed repair commit;
host metadata is observed rather than required to match a login-node kernel.
No reserved train/test data or private GIRO input enters.

Alternative: authorize no replacement and consolidate the LaTeX draft using the
already reviewed computational evidence. Describe the unexecuted retrieval
comparison as a limitation/future experiment, with no performance claim. In both
options, an ML study remains optional and there is no automatic further sweep.
