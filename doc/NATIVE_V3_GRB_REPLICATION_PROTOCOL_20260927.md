# Prospective V3 GRB qualification replication

27 September 2026. **Preparation only; no GRB qualification optimizer has run
under this addendum.** The already qualified CBC controls remain separate
evidence. GRB can have different solver behavior, so each GRB result needs its
own raw and target audit before use in the nonlinear pilot.

The physical stage uses the unchanged V3 20 controls (16 solution certificates,
four expected infeasibilities), targets, and one-thread budget: 10 seconds per
native phase, 45 seconds per control, 48 planner rounds, and a 60-second child
cap. It runs only through `experiments.native_v3_grb_replication physical` at
`result/native_pathflow_grb/20260927-attempt1`. The wrapper has a 1,320-second
process-group cap, covering all 20 child ceilings and 120 seconds of startup and
accounting. Its Slurm allocation is 30 minutes. A timeout, failed or unresolved
control, source drift, missing output or incomplete call accounting remains
failure evidence; there is no retry or resume.

**Pause after physical.** An auditor independent of the implementation must
review its frozen inputs, all 20 raw logs and receipts, GRB runtime identity,
expected statuses/targets, complete call and timeout accounting, wrapper
receipt, source hashes, and manifest. Only a passing review may produce
`doc/NATIVE_V3_GRB_PHYSICAL_ADMISSION_20260927.json` with `status: PASS`,
`backend: GRB`, `attempt: result/native_pathflow_grb/20260927-attempt1`, and
SHA-256 `pins` for `frozen.json`, `summary.json`, `grb_wrapper_receipt.json`,
`MANIFEST.json`, and
`doc/NATIVE_V3_GRB_PHYSICAL_RESULT_AUDIT_20260927.md`. The audit
Markdown must contain `**PASS**`. The adapter checks these pins, complete
20-control summary, wrapper/manifest, current shared physical source hashes,
and independent review before it will begin hull. A passing child return code
alone cannot admit the next stage. The hull job is separately submitted only
after this review and a new published source freeze that includes admission.

The hull stage uses the unchanged eight compact V3 controls, predecessor
states, targets, one-thread budget and native/polish limits; each worker has a
75-second cap and the existing hull supervisor has a 650-second cap with a
10-second TERM grace. It runs only through
`experiments.native_v3_grb_replication hull` at
`result/native_pathflow_hull_grb/20260927-attempt1`; its outer wrapper cap is
720 seconds and its Slurm allocation 15 minutes. The hull runner's CBC path
remains exactly `result/native_pathflow_hull/20260927-attempt2`; backend/path
crossing is rejected. No CBC archive is reused. Hull also needs independent
post-run raw and target audit before it can qualify a later public pilot.

Each stage requires a full published Git commit. The GRB wrapper freezes its
own source list, this addendum, batch scripts, controls and imported native
modules; child frozen source hashes must agree. The hull frozen source list
includes this addendum, and the hull wrapper also pins the physical admission.
The wrapper reserves a sibling `.launch` sentinel before starting a child,
runs it in a bounded process group, preserves stdout/stderr in that sentinel,
and writes a launch record, receipt and SHA-256 manifest to the exclusive
attempt. The sentinel remains after every exit and prevents a second launch.
The batch job writes its Slurm receipt to the sentinel, outside the sealed
attempt manifest. Both jobs require one CPU, 8 GB, no requeue, a clean checkout,
the exact full commit, `unicorn_env.sh` and GRB/license readiness. Preserve
raw license-bearing logs for independent review; do not publish them blindly.

These are GRB backend replications on fixed synthetic controls. They do not
show backend performance superiority, a public nonlinear optimum, or a
physical-versus-hull gap. No wrapper command is authorization to submit a job.
