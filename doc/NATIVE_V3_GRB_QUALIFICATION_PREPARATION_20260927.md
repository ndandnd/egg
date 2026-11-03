# GRB replication preparation: compact physical and hull gates

27 September 2026. Preparation only; no code or optimizer was run. Scope: the
unchanged V3 20 physical and eight hull controls, replicated on GRB pre-pilot.

## Current runner and protocol boundary

`experiments.native_pathflow_qualification` implements protocol
`native-pathflow-qualification-20260927-v3-orphan-projection`. Its CLI accepts
`--output`, a full `--freeze-label`, and `--backend GRB`; it attempts all 20
controls sequentially (16 certificates, four expected infeasibilities). The
budget is one thread, 10 seconds per native phase, 45 seconds per cell and a
60-second worker timeout, with at most 48 planner rounds. Its output path is
not tied to the local CBC archive.

`experiments.native_pathflow_hull_qualification` implements
`native-pathflow-hull-qualification-20260927-v3-orphan-projection`, accepts
`--backend GRB`, and runs its eight controls sequentially. Each worker is capped
at 75 seconds; the runner's process-group supervisor has a 650-second outer
cap and a ten-second TERM grace. The CLI nevertheless admits only the literal
`result/native_pathflow_hull/20260927-attempt2` path. That is the existing CBC
archive and must not be reused. The V3 hull protocol declares CBC as its initial
backend and says a later backend replication is separate evidence. It also
requires an independently audited V3 physical qualification before hull
execution; a same-job script must not skip that review gate.

## Recommended isolated GRB bundle

Treat this as one GRB replication bundle with two sequential Slurm stages and a
review pause, not as an automatic 28-control batch. First publish a short GRB
replication addendum that fixes the backend to GRB, keeps all V3 controls,
targets and budgets unchanged, and explicitly requires a passing independent
physical audit before stage two. Include that addendum in the frozen source
identity. Defer any runner/protocol edits until the active CBC eight-control
attempt is sealed.

The smallest hull-runner change is to replace its exact `ATTEMPT` path equality
guard with a fail-closed `--output` guard for a new, exclusive directory under
`result/native_pathflow_hull_grb/`. Keep `supervise`'s `mkdir(...,
exist_ok=False)` behavior. Add no resume, retry, or overwrite path. Pure tests
should allow a fresh path in that GRB namespace and reject the archived CBC
attempt2 path, an existing attempt, and a path outside the namespace. The
physical runner needs no output-path change. Re-run only its solver-free
preflight and the hull path-guard tests before freezing the resulting source.

After the full source state is reviewed and published, use a fresh isolated
worktree from that full commit. Leave the existing remote checkout at
`/home/nc437/egg-journal-public-20260927` (282e00b, with its untracked pricing
outputs) untouched. Use separate immutable, manifested outputs:
`result/native_pathflow_grb/20260927-attempt1` and
`result/native_pathflow_hull_grb/20260927-attempt1`, isolated from local CBC
archives.

Stage one runs the physical CLI with the full published commit as
`--freeze-label` and `--backend GRB`. Seal and independently audit all 20
controls, source hashes, GRB runtime/backend identity, raw outputs and complete
per-cell call/exit/timeout accounting. Preserve every failed or unresolved
cell; do not retry. Launch stage two only after that audit passes. Stage two
runs the hull CLI with the same commit label and backend; retain all eight
inputs, predecessor states, native/polishing events and receipts, final
summary, and supervisor receipt. Manifest each raw stage before review. Any
failed or incomplete stage blocks the nonlinear pilot pending review; it does
not become a passing GRB qualification.

Model each wrapper on `src/cluster/sistig_pricing_pilot.sbatch`: request one
CPU, 8 GB, `default_partition`, and `--no-requeue`; exclude
`scaglione-compute-01`, set single-thread numerical-library limits, verify the
full commit and clean checkout, then enter `src`, source
`cluster/unicorn_env.sh`, and return to the repo root. That environment requires
GRB and a readable cluster license and refuses silent CBC fallback. Run one
stage at a time, not as an array. A 30-minute
physical allocation covers its 20 x 60-second per-cell ceiling with controller
overhead; a 15-minute hull allocation covers its 650-second supervisor cap.
Write one wrapper `supervisor_receipt.json` per stage with job id, start/exit,
elapsed time, timeout state and return code; retain Slurm stdout/stderr and all
per-control runner evidence. The last queue check found no active EGG job; leave
other projects' held jobs untouched.

These runs, if later admitted, would be GRB backend replication on the declared
synthetic controls only. They would not establish backend performance
superiority, a public nonlinear optimum, or a physical-versus-hull gap.
