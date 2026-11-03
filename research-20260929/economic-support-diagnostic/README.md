# Run handoff

This package is one exclusive development attempt at
`result/economic_support_diagnostic/20260929-attempt1`. The Slurm wrapper
checks the clean published source commit, freezes the declaration on the
compute node, runs preflight, and supervises at most 12 bounded children.
It writes a wrapper phase receipt even if freeze or preflight fails. The
controller records six imported `CH` references plus planner and response
rows; ineligible response stages remain explicit and consume no solve.

Entry points: `python -m experiments.economic_support_diagnostic design`,
`freeze`, `preflight`, `supervise`, `controller`, and `worker` (see `--help`).
Only the root coordinator publishes/submits/collects this attempt. This
runner is a development evidence package, not a general solver workflow.
