# Independent implementation preflight review

27 September 2026. **PASS — implementation preflight only.** This review
covers the prospective one-cell controller and its protocol; it does not admit
or authorize a public run. The fresh same-source GRB physical-20 and hull-8
qualification gates have not run, and no nonlinear pilot or optimizer was
executed in this review.

## Reviewed artifacts

- `src/experiments/sistig_nonlinear_pilot.py` — SHA-256
  `36195617aa3b5b3955bea3f7fe04011a59d0c8d5458f20ad454a80944a7cb2de`
- `src/tests/test_sistig_nonlinear_pilot.py` — SHA-256
  `eb81b1868e24988645249c3acf2f9ab02c72b4d95a60b20e2d94188a96125d26`
- `doc/SISTIG_NONLINEAR_PILOT_PROTOCOL_20260927.md` — SHA-256
  `5fe33d06ddf1a52b611013932107bd2a8583cae02b7f3d9ffb0394a53ec0f326`
- `src/cluster/sistig_nonlinear_pilot.sbatch` — SHA-256
  `c3e2bef697d276cdfe66e1f1df06a7b4a7b932f4b0c8301305f836497fb07303`

## Findings

The runner pins the declared depot-15, all-37-service, 30-period, 30-hour
synthetic case and uses the accepted planner → cold hull → own-price sequence.
The 30-hour deadline is explicitly a finite service-block condition, not
recurring daily feasibility. Routine caps are 240/1440/240 seconds, child
caps 255/1455/255 seconds, and the total is 2040 seconds. The batch requests
one CPU and 8 GB, excludes `scaglione-compute-01`, disables requeue, and adds
the outer 2070-second timeout.

Admission compares JSON-canonicalized full physical-20 and hull-8 control
manifests, including control targets/state identities, against the current
qualification builders. It compares the complete GRB budgets and checks the
current physical and hull algorithm source hashes pinned by each gate. These
checks avoid requiring equality of unrelated publication commits. The frozen
attempt still pins all execution sources to its own published commit.

Hull results labeled `budget_exhausted` remain bounded only after the finite
global certificate and feasible mixture pass replay. The raw status is kept;
such results are not promoted to certified or optimal. Every final column is
replayed, while the saved mixture is reconstructed by its unique ordered
subset of column keys. Returned raw results are saved before assessment, so
an assessment failure does not erase solver output. A hard child timeout stops
the sequence.

Native module and archived-result contracts were checked alongside the
runner; the archived V3 hull schema includes the saved-mixture key subset
case. The pure suite passed (`13 passed`), including altered-control and
altered-budget admission holds, malformed/duplicate hull evidence, timeout
and failure receipt controls, and raw-result preservation. `bash -n`
passed for the batch script. No native optimizer or public algorithm was
called.

This is an implementation preflight only. Do not create the attempt or launch
the pilot unless a separate committed admission record pins audited,
same-source GRB 20+8 gate results and all protocol launch conditions pass.
