# Independent energy-V2 qualification result review

**PARTIAL / FAIL qualification gate.** The archived first V2 energy-band attempt passed 19 of its 20 controls: 15 certified numerical results and four expected infeasibilities. `joint_planner` failed extraction after its second native call. No downstream hull or operational admission follows from this attempt. The audit completed successfully; that does not mean the scientific gate passed.

The frozen source is `66b7054510a8b90471d6abe07d32a9f7f509182d`. The original `MANIFEST.json` SHA-256 is `dfd956c8da49d03bfec3db77a02396f8974ac4d6ba5ca3a95d713302fa33ebe3`. All 142 original files, totaling 686,302 bytes, were checked before and after the audit, with no changes. The twenty control definitions and all budgets match the closed compact V1 attempt. These derived files are excluded from the original manifest and have their own manifest.

The standard-library auditor imports no scientific implementation or native solver. It reconstructs every saved compact variable mapping, physical row, two aggregate energy rows, selection/path ownership, objective, normalization ledger and serial charging schedule. It independently replays all available physical witnesses and minimizes the fixture-specific global linear/PWL and true objectives. All twenty energy-band profiles have exact zero width; raw numerical residuals are still reported rather than called exact feasibility. Native execution identities identify CBC, one thread. All 30 calls returned: 26 `OPTIMAL` and four `INFEASIBLE`.

The complete reconstruction covers 26 incumbent snapshots and 479 raw variable values. Twenty-five snapshots have decoded witnesses, comprising 54 charging sessions and 202 post-initial SOC events across repeated rounds. Certified interval widths range from `1.999982956135682e-6` to `2.0000000517939043e-6`. The largest reconstructed raw row residual is `3.538502824085299e-12`; the largest energy-row residual is `3.5340619319867983e-12` kWh. The largest physical SOC residual is `2.1280754936015e-12` kWh. No negative charge variable was corrected. Ten decoded incumbents have positive serial roundoff ledgers, with maximum combined correction `7.105427357601002e-15` kWh, below the frozen `1e-8`-kWh budget.

## Failed control

In `joint_planner`, round 1 (the second native call) has exactly binary selections. Movement `in_A` has selection exactly zero but charge variable key `[1, 1]` equals

`378008408856669 / 309485009821345068724781056 = 1.2214110437041203e-12` kWh.

This is a tiny positive violation of charge activation. The frozen policy preserves positive energy, so the normalization stage retained it and the ownership check correctly raised `ValueError: Positive charge on an unselected movement`. The archive contains the full raw snapshot and accepted negative-normalization ledger, followed by the exception; it contains no decoded round-1 schedule or result certificate. The round-0 witness is available and was independently replayed, but it does not change the failed cell's status.

Both failed-cell calls returned `OPTIMAL`. Their saved PWL reference minima independently reconstruct as approximately `20.315789473684216` and `86.01385041551248`; reported objectives and bounds agree within the frozen numerical tolerance. The failed round has maximum raw row residual `3.2933655802480644e-12` and aggregate energy residual `2.129631312241243e-12` kWh. The failure is therefore an explicitly observed mismatch between native numerical feasibility and the stricter positive-charge ownership policy, not evidence of an exact physical witness. A future correction policy requires separate prospective versioning and qualification; this attempt stays failed.

## Verification and independence limits

All 37 deliberately corrupted copies were rejected. Controls include SOC, selection, resource capacity, exact correction amounts, objective/bound accounting, timing, missing evidence, altered aggregate coefficients/endpoints/row indices, failure relabelling, and silent removal of the positive orphan. Copies only were mutated. A portable copy ran with `mip`, `gurobipy`, `egglab` and `experiments` imports blocked. Existing output files and output paths inside a Git repository were rejected. Script portability and output protection were checked separately from scientific evidence.

The independent fixture core is preserved verbatim from the earlier review. The compact matrix auditor, originally written by a separate reviewer for V1, is adapted here for V2 identity and the two new energy rows. The reviewer participated in the analytical energy-band discussion but did not write or execute the scientific implementation. Independence is therefore from implementation and native execution, not from all project mathematics. The finite analytical fixtures permit independent objective checks; this audit does not establish arbitrary native lower bounds or operational performance. Witness claims remain conditional on the frozen numerical tolerances and roundoff policy, not exact repaired physical feasibility.

## Reproduction

Keep the four Python files together. From a checkout retaining the frozen Git commit and earlier fixture evidence, run:

```sh
python3 -B result/native_pathflow/20260927-attempt2/review/audit_energy_v2.py \
  --repository /absolute/path/to/journal-research-work \
  --attempt /absolute/path/to/journal-research-work/result/native_pathflow/20260927-attempt2 \
  --out /tmp/egg-energy-v2-new-audit.json
```

The output must be a new file outside any Git repository. The scripts can also be copied elsewhere and given the same explicit repository and attempt arguments. A zero CLI exit means that evidence reconstruction and corruption controls completed; consult `audit_status` and `downstream_admission`, which explicitly preserve **PARTIAL / FAIL** and `false` for this attempt. Runtime is the only nondeterministic report field.
