# Recovery1 focused checks

Checked locally on30September2026; no Slurm job submitted by this package.
No real TRAIN model fit, original outer result or inner metric was opened.

- `bash -n src/cluster/physical_route_model_families_v5_recovery1.sbatch` passed.
- Six recovery fixtures passed using `PYTHONPATH=src
  tmp/route-family-v5-env/bin/python -m pytest -q
  src/tests/test_physical_route_model_families_v5_recovery.py`. They cover failed
  task eligibility, original SIGILL wrapper/source/progress guards (including
  rejecting a truncated source-path map), native
  SIGILL surviving-parent receipts, stopping before training on preflight failure,
  exclusive no-retry directory, node/requested-CPU guards and timeout distinction.
- All five unchanged original v5 fixtures passed in the pinned local family
  environment with `DYLD_LIBRARY_PATH` set to scikit-learn's bundled `.dylibs`.
  These retain weighted inner-only selection, portable model roundtrips,
  best-iteration predictions, outer isolation and typed missing-dependency failure.
- Each recovery import probe and the32-row, two-tree synthetic fit/predict child
  completed locally with exit0. This validates the exact probe code locally; it
  does not establish the failed cluster nodes' ISA or prove Linux runtime success.
- `original_evidence` passed against the retained collected original artifacts
  for exactly task IDs0,1,4,5,6,7,8,9,11 and validated all18 original source hashes
  per task. It read only launch/source_identity/wrapper metadata and directory
  presence, without opening result or candidate metric files.
- Read-only `scontrol show node` inspection via unicorn2 corroborated the node
  features/topology described in the recovery protocol. No additional queue or
  accounting polling, native import probe on a login node, dependency installation,
  shared-environment mutation, commit, push or submission was performed.

Cluster failure localization remains prospective: `SIGILL` and node correlation
are demonstrated, but the offending library/instruction is unproven. A new
recovery launch must be recorded by root and separately reviewed before dispatch.
