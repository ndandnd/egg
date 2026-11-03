# Independent V3 compact-hull implementation review

**PASS — preflight only; the public-case algorithm was not run.** Reviewed the
V3 policy integration at the source state recorded below. No optimizer was
started. This review is an independent check of the implementation and
prospective protocol, not an independent audit of any V3 hull result.

The indexed default keeps its original `nr.EXTRACTION_POLICY`, state digest,
dispatch, result shape and coordinator behavior. The pure tests reconstruct the
default digest payload directly. The V3 adapter passes its own extraction
policy and oracle identities explicitly. Result and plan tags are required on
each compact pricing response; compact columns, plans, coordinator results and
state identities carry the V3 policy. Replay and retained-pool import validate
the explicit policy, and retained states cannot cross the V2/V3 boundary.

The scoped review caught and closed one low-level cross-policy gap before
approval: the indexed-default `native_column` and `replay_column` paths now
reject an explicitly conflicting nested plan policy, while still accepting
legacy pure-test plans with no policy field. A targeted forged-plan/hash test
covers both operations. This protects direct helper use as well as the normal
coordinator path.

I independently loaded the archived attempt1 `frozen.json` (SHA-256
`eba73e27a69c66c64d777d3899acee46156e6ff8147109cd55c6ba6a2182a3da`) and
compared its eight controls with JSON-canonicalized V3 manifests. Definitions,
targets, labels, market coefficients, predecessor links and state order match
after excluding only the expected V3 oracle/policy metadata and
policy-dependent state digest. The CBC budget is exactly identical, including
`1e-4` certificate width, `1e-6` pool tolerance, 16 pricing calls, 64 masters,
48 columns, 10-second native phases, 60-second state wall, and exact-polish
limits of 256 steps, 8,192 rational bits and five seconds. Worker and outer
caps remain 75 and 650 seconds. The current V2 energy-band protocol is
byte-identical to the source-frozen copy at commit
`66b7054510a8b90471d6abe07d32a9f7f509182d`.

The prospective 19-entry source manifest includes the shared `native_hull.py`,
compact adapter and physical model, both relevant runners, the modified fake
fixture, the new policy tests, and V3 design/protocol documents plus this
review. All entries resolve now, and the runner computes a digest for each,
including this saved review, at any later freeze.

Validation run:

```text
PYTHONPATH=src ../.research-venv-repaired-1176/bin/python -m pytest -q \
  src/tests/test_native_hull.py src/tests/test_native_pathflow_hull.py \
  src/tests/test_native_pathflow_hull_policy.py
96 passed
```

The tests block native optimizer imports. They cover indexed default digests,
exact eight-control parity, explicit V3 dispatch and tags, replay and retained
import boundaries in both directions, V2-to-V3 identity separation, the
indexed-default conflicting-plan rejection, and worker admission. The
prospective attempt remains manager-owned; this preflight does not freeze,
authorize or execute it.

## Reviewed source hashes

| File | SHA-256 |
|---|---|
| `src/egglab/native_hull.py` | `ef7b3ee5a3ab7f11a48a92c1dc4a055d598b609ba4af70b77b2aa38c3277e5cb` |
| `src/egglab/native_pathflow_hull.py` | `853e590ce6d25c044c5c5c70bfeb04d0d3a3dde56a4144a1d746fad55cf87338` |
| `src/experiments/native_pathflow_hull_qualification.py` | `24b6b0c32afdf40117a65b2c5c10626c541c0904233ff24aae7c23a705eb3ca2` |
| `src/tests/test_native_pathflow_hull.py` | `354c518e394302c46dee7aead98b20e9b35244caa4c503f2912a3781c190f891` |
| `src/tests/test_native_pathflow_hull_policy.py` | `1891ddbded90507835b7c9bf93ef3b36b99d484ed281d8311fa3e47e07f48f0b` |
| `doc/NATIVE_PATHFLOW_HULL_V3_QUALIFICATION_PROTOCOL_20260927.md` | `f615369098db9a01c164d0ae840203a859d378e0986bde21ab8499fea09bf6c0` |
| `doc/NATIVE_PATHFLOW_HULL_V3_POLICY_INTEGRATION_20260927.md` | `7817c87862ef466c5f64c3ef0cbdc3611035120c85c1d1e035505bf0f55d10cf` |
