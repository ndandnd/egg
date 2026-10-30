# Independent preflight: complete Sistig pricing pilot

27 September 2026. **PASS for the prospective bounded two-cell design at the file hashes below.** No optimizer or cluster job was run by this review. Execution and result audit remain separate gates. This independent reviewer did not author the pilot runner, physical formulation or protocol.

## Scope and prerequisite

The pilot retains all 37 services and the complete declared graph separately for source depot 15 and source depot 16. These are two single-depot adaptations, not the source two-depot problem. The flat 0.2 price, 100 vehicle cost, modeled energies, battery and connector assumptions are synthetic. Neither the source published schedule nor the constructive 37-bus witness is supplied as a solver seed.

The runner hashes the twenty-control compact gate's frozen input, raw manifest, summary, independent review manifest/report/note. It requires the gate summary to pass with unchanged source, requires its independent report to pass all twenty controls, and matches the current compact and physical source hashes to that gate. The inspected gate freeze is `ebb146e9de01d0c6aa13b03eb2348337a1d0b3f0` (saved short label `ebb146e`). Its separately authored independent audit reports twenty admitted controls and 25 corruption rejections. This preflight verifies those dependency records and source matches; it does not relabel that other review as a new independent execution here.

## Reviewed admissions and repaired findings

The final runner checks returned case identity and the complete price vector. It independently reruns physical replay and the unchanged native-bound admission policy, requires exact equality of the resulting displayed enclosure endpoints, validates GRB backend/module/thread identity, and cross-checks the lower bound against the constructive feasible reference. A finite wide enclosure is explicitly `bounded`; only width at most 1e-4 is `certified`. A native infeasibility or missing incumbent conflicts with the known feasible reference and fails this pilot. A bounded success must not later be represented as an optimum.

Earlier review findings concerned admission of an unsupported lower bound, incomplete phase identity/accounting, and omitted solver/environment dependencies. The inspected revision repairs them. Finite results require the unique ordered round-zero six-event linear phase, raw native-status statistics equal to result statistics, complete nonzero start/return accounting, successful child exit and an affirmative assessment. Truncated evidence preserves its readable prefix and fails closed. Each cell has an exclusive directory and the controller attempts the second independent cell after a first-cell failure. Scientific source hashes are checked before each solve and at controller completion.

The complete source payload is pinned by SHA-256. The adapter reconstructs both identities from this payload, checks service count/depot order and replays its reference. No source download or publisher optimizer is part of execution. Dataset DOI, license, adaptation and compact-gate identity are written into the freeze.

## Independent constructive reference

Using only the shipped JSON, standard-library rational arithmetic and the stated physical rules, this review reconstructed 37 dedicated-service buses in each scenario. For every bus, the unique pull-out, service and pull-in consume less than its 400-kWh usable capacity; starting full gives a monotone nonnegative SOC before terminal charging. Terminal jobs are ordered by arrival and service ID, each starting at the later of its release and the previous job's finish. Duration is exactly 60 times grid energy divided by 360 kW. This proves one-connector non-overlap and full terminal replenishment without an optimizer.

| Scenario | Total grid energy (kWh, displayed) | Reference objective (displayed) | Final charge finish (min) | Maximum individual energy (kWh) |
|---|---:|---:|---:|---:|
| Depot 15 | 2089.8764409985943 | 4117.975288199719 | 1490.5238145685698 | 59.33457453406491 |
| Depot 16 | 2769.8144794193886 | 4253.9628958838775 | 1501.1225345685698 | 81.3648273318893 |

Both finish strictly before 1800 minutes. Exact total energies from binary-stored inputs are `294123961279114003/140737488355328` and `779633466087410129/281474976710656`. All input time values examined are on the qualified nonnegative half-minute lattice (5,370 values for depot 15, including 1,676 non-integers; 5,230 and 1,299 for depot 16). The reference establishes feasibility and an auxiliary upper bound, not a minimum fleet or optimum. Its displayed values remain subject to the documented stored-float/numerical policy.

## Resource envelope and checks

The wrapper fixes explicit GRB, one solver thread, one CPU, 8 GB, 12 minutes, excluded busy node and no requeue. Per cell: 180-second native phase, 240-second routine deadline, 255-second child hard timeout. The sequential wrapper's 560-second hard stop is a kill margin, not additional scientific compute. It requires the exact frozen Git commit and no tracked dirty files. The shared environment's backend probe constructs an empty backend model for availability; source inspection found no optimization in that probe. It has no fallback to another solver. Live cluster policy/queue checks remain the root's execution responsibility.

Independent checks: five pure/fake tests passed in 0.19 seconds with imports of both `mip` and `gurobipy` externally blocked; `bash -n` accepted the batch wrapper. Adversarial tests cover unsupported bounds, mismatched identity/prices/status, malformed enclosure, replay rejection, missing/reordered/duplicate/foreign-round events and raw-status mismatch. These checks validate admission logic, not operational runtime or solver feasibility on the 37-service models.

The final protocol agrees with the runner's destination, gate, admission deadline and publication policy. Two final accounting alignments were independently reviewed: the worker now measures the scientific routine plus replay/admission and rejects elapsed times exceeding 240 seconds while retaining the returned scientific result and raw trace; the 255-second hard limit covers final serialization. The batch wrapper now writes an exclusive supervisor receipt with the timeout command return code, start UTC, whole-second elapsed time and 560-second/10-second kill policy, then preserves that exit code. Slurm cancellation or abrupt node loss can still prevent a shell receipt; such missing evidence must remain unresolved and be diagnosed using the immutable Slurm records. These changes do not change physics, targets or numerical tolerances. Keep the full original archive immutable. A separate public copy may omit a verified sensitive stdout file only with its original length/hash/reason recorded; numerical/input/event evidence stays byte-identical. This preflight contains no license identifiers.

## Reviewed SHA-256 dependencies

- `src/egglab/native_recharge.py`: `0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3`
- `src/egglab/native_pathflow.py`: `45864e08bffb81dc29b27774449f944fd074cb6654a593ab0d482abdad935c7d`
- `src/experiments/native_recharge_qualification.py`: `200c5bec8e6f8c7f7e466ef045b439dceae9fa2b35984cc452d4d29471dfde1e`
- `src/experiments/sistig_native_case.py`: `f47a7a926d102f948d73e6d450f25a46fe7ad84fc93e4ff7e877da76ffe0e3c9`
- `src/experiments/sistig_pricing_pilot.py`: `5cd418f87616a1fbd4749dc4c7f8590a1188d83b22b643a100562554ce7eca9c`
- `src/tests/test_sistig_pricing_pilot.py`: `d0bf0a8e247f44057a881cfbcb013427e4c91bd45a71f016d0d38f0e3a4068c0`
- `doc/SISTIG_PRICING_PILOT_PROTOCOL_20260927.md`: `819eb70f85a51bc37a3c6054801e1eafd6320ae119a7c5eea8066eb05e136cb3`
- `src/cluster/sistig_pricing_pilot.sbatch`: `b4344530a6b6ac5abf67aae259ddd4108daf60487b902dec15a2ade02606bb3b`
- `src/cluster/unicorn_env.sh`: `1731f65b21fd9c81f5726078490aed384974ac2e4869bdc13e7259d5ab045678`
- `src/egglab/solver.py`: `4d5ea429a84441d20b23856d903f9a499cb1e7e2d51ec61e6c163617478c6074`
- `result/native_pathflow/20260927-attempt1/frozen.json`: `d34dd723415c2e03f1b06a01621cbcb54557dc6eeb52550b2a5dbaa5fbfe25e4`
- `result/native_pathflow/20260927-attempt1/MANIFEST.json`: `2ab225a5b79cf278c5ef55c834ba835a65126f09f370b9b967e5fac8a2f5327d`
- `result/native_pathflow/20260927-attempt1/summary.json`: `4b980b32cce6bda057c2f727d7a4ecc3b379e54cfd4a41214487c33408578f03`
- `result/native_pathflow/20260927-attempt1/review/MANIFEST.json`: `ebb85951b4a422f282933d9cdbc99a44ce7a957d191ece4dd58e9cf22fd354dd`
- `result/native_pathflow/20260927-attempt1/review/audit-report.json`: `560caf8d0e48789a7b76749f6ba422d64a118d30a38edd79e84a9074db6a4de8`
- `result/native_pathflow/20260927-attempt1/review/REVIEW.md`: `08d9d7dcae6f8b1d3b224166b4805792c102ad294ff28bebe77e59c3c9647b69`
- `data/public/sistig_26088190_v1/hildenbrand_native_cases.json`: `af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6`
