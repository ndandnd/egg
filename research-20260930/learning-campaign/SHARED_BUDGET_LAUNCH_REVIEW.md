# Shared-cover budget study launch review

The shared-interval screen produces two physically replayed four-bus fleets on
the 20-service development timetable. Both 28-service arms reach the five-second
cover limit without an integral incumbent. This is a time limit, not physical
infeasibility. One separately frozen two-arm study with a 30-second cover cap is
justified; the model, timetable, objective, physical constraints and other limits
remain unchanged. The order preserves learned then cost-only for this case.

Root reviewed the explicit profile subset, cell guard, budget propagation through
worker and repair, per-stage receipts, frozen design and prospective protocol.
The subset prevents 20-service work in this attempt. Cost-only still receives no
model; prior profiles keep four cells and five seconds. Positive shared-charge
witnesses remain available. New candidates require native charging and replay;
failed proposals retain evidence and use the archived fallback without repeating
its hull check. The unchanged 240-second child limit covers the prospective
30-second cover, 55-second charging wall and 70-second hull wall budgets plus
setup, and remains a hard cap rather than a promised execution time.

GPT-6 Sol's final affected suite passed 42 tests and 8 subtests. Wrapper syntax,
two-cell/30-second frozen design, 54 unique source pins and diff checks passed.
Independent replay of all four preceding outcomes and shared charge witnesses
passed without optimization. Local tests used only small HiGHS fixtures and
archived inputs; no local GRB or new full development fleet optimization ran.

One serial job requests one CPU, 8 GB, 30 minutes and one native thread, with
no retry/requeue and exclusion of scaglione-compute-01. The helper guards active
EGG jobs and requires a fresh checkout. No refit, reserved-test access, added-bus
heuristic or automatic rerun. Root found no launch blocker. Separate launch
receipts record the reviewed commit and job ID; no new outcome is claimed here.
