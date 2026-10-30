# Nonlinear timing amendment review — 27 September 2026

**Recommendation only; not an implementation approval or launch authorization.**

## Failure boundary observed

At source freeze `80eb69544f56`, the sealed attempt1 summary records a worker
elapsed time of 242.315 s and return code 2; the worker raised `Scientific
routine/admission cap exceeded` at its unchanged 240 s guard. The planner
child took 243.218 s; the supervisor took 243.348 s overall. This was not a
hard timeout. The raw return and exception were retained; the source check
passed. Hull and own-price were unstarted. Attempt1 remains a failed attempt
under its frozen protocol and must not be reclassified.

## Prospective attempt2 reservation

Keep the end-to-end scientific routine caps at 240/1440/240 s, child hard
caps at 255/1455/255 s, the total supervisor cap at 2040 s, and batch wrapper
at 2070 s. Keep one CPU, 8 GB, no-requeue, reserved-node exclusion, and freeze
inside the batch job. Add explicit internal wall reservations while retaining
the existing end-to-end worker guards:

| Stage | Routine cap | Proposed native `wall_seconds` | Reserved within routine cap |
|---|---:|---:|---:|
| Planner | 240 s | 225 s | 15 s |
| Full-fleet hull | 1440 s | 1380 s | 60 s |
| Own-price response | 240 s | 225 s | 15 s |

These are conservative prospective allowances for model setup, extraction,
replay, assessment and receipt work; they do not add runtime or loosen a
guard. Preserve 180 s phase caps, planner 48 rounds, hull six pricing calls,
eight masters, 48-column pool and all polishing caps, and one own-price call.
Keep the case, stored objective, solver/backend, result-admission rules and
stage order fixed. Valid bounded returns remain bounded under existing rules;
missing evidence, a stage cap breach or hard timeout still stops the attempt.

## Required identity and test edits before any freeze

1. Runner: use protocol `...-v2`, exclusive `20260927-attempt2`, separate
   routine caps from the reserved native wall budgets, and freeze/check both.
   Keep 240/1440/240 elapsed guards, 255/1455/255 child waits, 2040 s total,
   failure receipts, raw-before-assessment writes, cleanup and write-once.
2. Pure tests: assert exact stage-budget values and reserve arithmetic; reject
   mutated reservation/budget maps; retain bounded evidence at a valid stage
   elapsed below its routine cap and reject a cap breach. No optimizer fixture
   or result from attempt1 is an admission input.
3. Protocol: state the reservation table and unchanged scientific caps,
   unchanged phase/call limits, attempt2 path, fresh source freeze and failure
   semantics. Update the implementation review for this prospective identity.
4. Batch: change only the exclusive output path to attempt2; preserve one
   freeze inside the job, 36-minute allocation, 2070 s shell stop, 1 CPU, 8 GB,
   no-requeue and reserved-node exclusion. Pin the revised script hash in the
   fresh freeze; change no resource or timeout directive.

The admitted GRB 20-physical/8-hull evidence remains applicable if native,
formulation, case, qualification helpers and gate dependencies stay byte-
identical. Production wall allocations are separate from qualification gate
budgets, which must continue to match exactly. Publish and independently
review the revised runner, tests, protocol and freeze before one attempt2
dispatch. No optimizer was run for this review.
