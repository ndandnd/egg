# Independent preflight: compact pricing in native hull

27 September 2026. **PASS for the narrow prospective integration at the dependency hashes below.** This review executed no optimizer and made no changes to scientific source. A separately frozen first eight-cell integration attempt and independent raw-result audit are still required. The earlier indexed V2 attempt remains tied to `186c9876805d5096632786c5504f507847a5201f`; its completed independent review is separate from this prospective source review.

## Scientific contract and unchanged implementation

The only altered existing shared definitions are `native_hull.state_identity` and `native_hull.certify`. An AST comparison against frozen indexed V2 confirms all other function/class definitions are unchanged. The indexed physical/replay source, compact physical source, indexed qualification runner and original 64-test suite are byte-identical to that freeze. In particular, exact simplex normalization, aggregate nonlinear cost, bounded rational pairwise polishing, outward rounding, actual serialized-price conjugate, pricing-bound admission and all master calculations remain shared and unchanged.

The new adapter explicitly supplies the already qualified compact complete-fleet price oracle. The underlying integer compact formulation and indexed formulation have the same physical feasible set and cost/load projection under the existing homogeneous-fleet, directed service DAG, prescribed movement and finite one-connector assumptions; the earlier compact equivalence/physical qualification establish that premise. This preflight does not assert equality of their LP relaxations or runtime.

An independent comparison against all eight serialized indexed V2 inputs confirms that complete cases, coefficients, targets, predecessor links, state ordering and every budget field are unchanged. Default indexed state digests remain exactly equal for all eight cases. Compact digests differ by their explicit pricing-oracle metadata. This is a new implementation integration gate, not new synthetic evidence until execution and audit.

## Explicit dispatch and retained identity

The hook requires both a callable and a nonempty explicit oracle identity, or neither. With neither it retains the original indexed callable, digest payload and result/event metadata shape. With the compact adapter it calls the compact price function directly without changing a global binding. Before every pricing admission, including later calls, the coordinator requires both returned result and physical plan tags to identify the requested formulation, then applies the existing case identity, submitted prices, physical replay, objective and global-bound admission.

The qualified compact V1 driver already tags its raw snapshot and physical plan, while its top-level result has no formulation field. The adapter verifies the physical plan's existing tag for a finite admitted status, rejects any contradictory top-level tag, then attaches the explicit dispatch tag. This is legitimate frozen-call-path provenance; it is not cryptographic evidence that an arbitrary external callback implements a declared mathematical set. Missing/nonfinite/unresolved results cannot be certified by adding a tag.

Retained import verifies the top-level oracle identity before importing any pool, as well as the unchanged immediate predecessor identity/status, controller admission and complete physical replay of every column. Both indexed-to-compact and compact-to-indexed imports are rejected. Whole physical columns remain the transferable objects; prices, bounds, weights and tangent cuts are fresh. The existing predecessor helper also requires a zero exit code, no timeout/issues, complete nonzero native work and matching polishing accounting.

## Controller and evidence

The new runner owns its worker/controller module dispatch and exclusive attempt namespace. The supervisor runs a new process group, caps it at 650 seconds and terminates surviving group members; each sequential worker retains the unchanged 75-second external cap. Failed independent cells continue and failed predecessor chains block. Source hashes, new protocol and explicit oracle identity are checked before a worker calls the optimizer. Complete inputs for all eight cells are written before any worker execution.

The runner imports the reviewed V2 fixture, assessment, parsing, accounting and predecessor helpers explicitly. All runtime scientific dependencies and both old/new qualification protocols/tests are included in the 13-entry source manifest. No source data, public timetable or cluster operation is added. Native and polishing caps, status gates, raw evidence and failure preservation are unchanged. The inherited 60-second algorithm deadline supplies remaining-time limits to native phases and polishing; the separate 75-second process cap is a kill margin. As for indexed V2, a result audit must inspect actual saved elapsed times; this preflight does not independently authenticate runtime or extend any budget.

## Verification and limits

All **79 pure/fake tests passed in 0.35 seconds** with `mip` and `gurobipy` imports externally blocked before test/module import. These include the unchanged 64 V2 tests and 15 compact integration cases covering default dispatch and digest compatibility, complete eight-state fake execution, missing/invalid dependency pairs, later-call result/plan formulation mismatches, both retained-boundary directions, compact worker dispatch and continued processing after independent failures. Independent serialized-input and AST comparisons supplement these tests.

No new blocking source defect was found. Passing this preflight is not evidence that the native compact hull algorithm converges within its frozen budgets: the prospective first attempt must retain every failure and undergo a separate solver-free audit of compact raw constraints, physical witnesses, full-pool mixtures, pricing lower bounds, polishing equations, certificate widths and receipts. No claim about operational public inputs or speed follows from this small gate.

## Reviewed SHA-256 dependencies

- `src/egglab/native_hull.py`: `335143dc4bdfff71193962038de0b74f77b6b5c6f4955ba2d56713c3c75a19d1`
- `src/experiments/native_hull_qualification.py`: `4129080d33dd474e4296a02fcc4af5feb18051be814bde016edf3f5450eb8d30`
- `src/tests/test_native_hull.py`: `9a7c5ab571b35b407d393f03bf38eb6e5f0e8381ee163fead37a3439c7943f32`
- `doc/NATIVE_HULL_QUALIFICATION_PROTOCOL_20260927.md`: `4a88398af643902ff7a25c0a0008612eae79300a5347c87a9c9dc7d70785bd4a`
- `doc/NATIVE_HULL_CERTIFICATION_DESIGN_20260927.md`: `690fdbdafe65102a845d4f052f737cf1a9ec938562b360bfa1a06e12f4114a0f`
- `src/egglab/native_recharge.py`: `0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3`
- `src/experiments/native_recharge_qualification.py`: `200c5bec8e6f8c7f7e466ef045b439dceae9fa2b35984cc452d4d29471dfde1e`
- `src/egglab/native_pathflow.py`: `45864e08bffb81dc29b27774449f944fd074cb6654a593ab0d482abdad935c7d`
- `src/egglab/native_pathflow_hull.py`: `60ed3a30cbce990649efad26405354cfa6c343a1c0b5bdaf010c3338b42a8686`
- `src/experiments/native_pathflow_hull_qualification.py`: `f5ab5e73c727a04debc23403a8332f0f3b45121b4a150827969638f720ac0358`
- `src/tests/test_native_pathflow_hull.py`: `3cc9dab5b4790311a30911d0607e8b5156077f307c4d93639446ad3edd2713a9`
- `doc/NATIVE_PATHFLOW_HULL_QUALIFICATION_PROTOCOL_20260927.md`: `9ce36a49fe449f55ff1b38993fc3c5f8c39bbeec255bfe24004d9b8a441f71cd`
- `doc/NATIVE_PATHFLOW_HULL_INTEGRATION_DESIGN_20260927.md`: `5bffa264ea89f23bddf8fa101f04c1f10ca6c3d86f1dd349dcd852fd3b9756ee`
