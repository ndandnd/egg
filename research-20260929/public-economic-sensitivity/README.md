# Exclusive attempt handoff

This package runs only at `result/public_economic_sensitivity/20260929-attempt1`.
The scheduler script requires a clean published checkout and `EGG_RUN_COMMIT`,
then freezes and preflights on the compute node before supervision. The
wrapper writes setup/phase/whole-job receipts even if an early phase fails.
The controller attempts planner and hull for each of eight cells, then a
response only when its own planner produced on-time replayed evidence.

CLI modes: `python -m experiments.public_economic_sensitivity design`,
`freeze`, `preflight`, `supervise`, `controller`, `worker`. Root owns remote
publication, exclusive checkout, launch and collection. This is one bounded
development block; no automatic sweep expansion or failed-attempt retry.
