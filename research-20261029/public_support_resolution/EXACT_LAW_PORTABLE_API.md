# Exact-law portable verifier: narrow source/API feasibility

**FEASIBLE with three exported mathematical checkers and a new thin adapter.** The retained LOWER packet is NOT a standalone375-node proof: it contains an audit/result, not the input tree. The retained target case and two NEW target candidates are sufficient for model/witness input; the303-node tree and72-child refinement proposals must be grafted once. No discovery, solver, face recovery, route/weight optimization or original-law audit is needed.

This is source-only API discovery after the parent's explicit portability-purpose decision. Read only named packet writers, return schemas, prepare/verify dependencies and original portable CLI/assembler interfaces. No actual packet decoding, imports, hashes, compilation, numerical tests, evidence replay, old exported bundle or solver was used. No implementation or dispatch is authorized by this note.

## Immutable sources and minimal closure

| File | Revision | Needed API/role |
|---|---|---|
|`public_exact_energy_target/target_semantics.py`|`6665c2b9f045410b4bbf19060b6780b0779f5534`|`_reconstruct(case)` returns variables,rows,intervals,operations,loads,fleet_proof; rational energies, original binary nonenergy semantics.|
|`public_support_resolution/independent_verify.py`|`3278d50f8323618bd36809b1bbb1a0da081e23ff`|`verify(case,candidate)` independently reconstructs paths, intervals, exact loads/cost and strict SOC/full refill.|
|`public_support_tree/checker.py`|`6a171357b65254b52cade63ed95dcce798485f36`|`prepare(case,reconstruct,mode='quadratic',fleet_count=2,case_token=TARGET_ID)` and `verify_tree(...)`; all dual/box/tangent/Farkas algebra is INTERNAL.|
|`public_exact_energy_target/checker.py`|`6665c2b9f045410b4bbf19060b6780b0779f5534`|`graft_proposals(original,refinement,expected=(303,152,72))`, `stripped_certificate`; needed during trusted local assembly, or translated into a reviewed adapter.|

All paths in this table are relative to `research-20261029/`. The three mathematical modules import only stdlib. **Frozen `exact_dual.py` is NOT an execution dependency of the tree checker.** Its name appears in the callback documentation, but `prepare` only calls the supplied six-tuple reconstructor; `_node` implements the exact residual bound itself. The target semantic module has removed its unused old dual-verification APIs and does not need them restored.

The assembler can use the fourth frozen helper to create a normalized, scalar-stripped combined tree, then export ONLY that tree. Standalone verification needs the three modules above plus a new source-pinned CLI. Alternatively the CLI can receive both raw tree packets and include the narrow graft adapter; this avoids a generated normalized-tree artifact but carries larger/less minimal inputs. Do not reuse the original-law `graft_tree` blindly: target grafting deliberately STRIPS historical bound/contradiction claims before fresh target evaluation.

`public_certificate_bundle/bundle.py` and `verify.py` supply SOURCE-ONLY interface patterns, not reusable frozen target semantics. `build(repo_root,out_dir,source_revision,source_buffers=None)` pins/caches bytes, writes an exclusive local bundle and manifest, and returns a separately trusted manifest digest without verification. `verify_bundle(directory,expected_manifest_sha256,limits=None)` performs the retained check. CLI is `python -I -S -B verify.py --manifest-sha256 DIGEST --output verification.json`, with root taken from the script. Their old case token, binary case parser, candidate extraction, old bound constant and member list MUST NOT be copied unchanged into a target consumer. No original bundle needs reading.

## Exact retained schemas established from writers

All target packets below are at `d27f9f13ff8e61721dda39ee680be612c01c8ecc`, under `research-20261029/public_exact_energy_target/attempt01/`.

### TARGET.json.gz

Writer returns exactly the documented outer fields:

`status,record,validated,manifest,old_gap_transferred,native_calls`.

The authoritative DECLARED target case is `packet['record']['case']`; validation also retains `packet['validated']['case']`. Validate agreement on those projected cases and target identity before exporting, without recursively processing unrelated diagnostics. `validated` returns:

`status,identity,old_identity,case,ledger,policy,denominators,row_substitution_scope,old_gap_transferred`.

The ledger is the exact six-tuple, but a fresh portable checker MUST reconstruct its own target ledger from the declared case, not trust the serialized ledger. Expected counts are37 services,1370 modes and2648 legs. Target identity is

`1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7::exact-consumption-v1`.

The NativeCase dictionary itself keeps the original schema/name and original numeric nonenergy fields; the new identity is outside that dictionary. Decode JSON nonenergy numbers as int/float, preserving their binary64 interpretation. **Do not use `parse_float=str` for the exported target descriptor:** `_source_number` intentionally rejects string nonenergy fields. Exact ENERGY fields are canonical nonnegative integer/fraction strings, not floats.

### INCUMBENT_ROUTES.json.gz and RESPONSE_ROUTES.json.gz

Successful target witness packets put the complete new candidate at TOP LEVEL `packet['candidate']`, NOT `packet['recovery']['candidate']`. The latter is the historical proposal schema and the original-law portable extractor's schema; using it here would recreate an avoidable interface failure.

Strict allowlist for portable physical evidence:

- `candidate.selected_movement_ids`: complete ordered unique movement IDs;
- `candidate.charge_by_interval`: every unchanged record with `movement,interval,energy`;
- target identity/status and claimed `loads_exact,ops_exact,objective_exact,fleet_count,a_exact,b_exact` for comparison against fresh replay.

Preserve every selected ID and allocation/zero record, with exact energy values. Do not repair, regrid, adjust terminal charges, recover a face or choose a different route. Optional candidate `load,ops,soc` fields may be preserved for additional exact agreement checks; they are not required by `verify`, and any omitted auxiliary fields should be disclosed. Do not export/seal `problem`, `values`, RREF/dual/recovery matrices or unrelated diagnostics. The original immutable full packets remain untouched.

`verify` requires all three booleans `strict_pass`, `physical_strict_pass`, `objective_is_certified_physical_upper` to pass. It returns fresh `loads_exact,ops_exact,objective_exact` and rational violations. The standalone check should compare these fresh results with the projected claims; admission flags in the input are not proof. Existing source proposal bounds are5000 IDs and10000 allocation cells; any new explicit wrapper schema bounds must be frozen, not inferred from unseen packet contents.

### LOWER.json.gz

Writer returns `status,target_identity,lower,audit,reason,physical_only_not_CH,old_claimed_scalars_used_as_proof`. `audit` contains checked leaf results/coverage. It does **NOT** return the assembled `proof` or preserve the full branch tree: that local object is consumed by `verify_tree` and omitted from the return. Thus a source-bound LOWER scalar/audit alone cannot supply a fresh standalone tree verification.

Use these retained proof INPUTS instead:

- `ef0e08203dba5ac2ddcaff6bd8639cc9a70677b9`, `research-20261029/public_support_tree/attempt01/PUBLIC_TREE.json.gz`;
- `d8e22ffd3753fced3ec825c68714fd549d914230`, `research-20261029/public_physical_refinement/attempt01/PUBLIC_REFINEMENT.json.gz`.

`graft_proposals` reads original `case_token,tree.root,tree.nodes,proofs[certificate_ref].certificate` and refinement `refinements[old_leaf_id].root/nodes,proofs[certificate_ref].certificate`. It requires303 base nodes, all152 original fringe IDs and72 added children, resulting in375 nodes. Both binary children must remain. Inherited old contradictions require fresh target Farkas checks; no old infeasible status rescues a failed target proof.

The old `claimed_lower` is used ONLY to select between fixed retained multiplier proposals. After selection, `stripped_certificate` exports just `multipliers` and, for bound leaves, `tangent_loads`. It removes all old claimed lower/contradiction/status fields. A normalized export should contain branch nodes `kind,movement,children{'0','1'}` and bound/infeasible leaves `kind,certificate`, plus root and fixed identity/count metadata. Fresh target verification then supplies every mathematical lower/contradiction value and full root-to-leaf coverage, ONCE on the combined375-node partition. There is no separate original303 numeric audit.

### Fixed mixture and claimed new conclusion

Use `research-20261029/public_exact_energy_comparison/attempt01/COMPARISON.json` at `fdb85682cf6476227d6fa8fb8258613f512d65d4`. Project target identity, `lambda_left,lambda_right` in incumbent/response order and exact claimed `lower,upper,gap,physical_upper`, with outward units optional. Recompute the FIXED mixture from the two fresh replay loads/ops and original binary a=.2,b=1/900. No historical mixture packet, old objective, weight optimization or variance helper is necessary for mathematical sufficiency; the retained independent variance result is provenance, not a substitute for fresh feasibility.

The fresh physical lower must be global: reconstruct minimum_fleet_proof>=2, build the source-bound TARGET typed `physical_ge_3` affine service floor using target service energies, then let the immutable tree checker independently recompute/validate that floor. The floor is `3*fee+binary_a*sum(target service energy)/eta`; do not transfer the old numeric floor. With exact-two tree plus these exclusions, compare global physical lower to the new feasible hull upper and to the smaller fresh physical upper. Require the published target claims to agree at the chosen declared equality/at-least policy; no CH lower or exact optimum is established.

## Bounds already present in source

These are existing prospective SOURCE bounds, not measured packet sizes:

- Original portable manifest:1MiB; each member compressed/read bound512MiB; decompression512MiB per member; total consumed member bytes1GiB; symlink/path containment and exact member closure checks.
- Target producer consumes/decompresses each packet with512MiB bounds. No new actual target output byte count was read here.
- Target energy parser:4096-character canonical token and32768 numerator/denominator bits; exact target proof helper:32768-character rational text, no exponent,32768 bits.
- Target tree:375 nodes/depth375,100million operation checkpoints,32768-bit arithmetic; the original target phase allowed850 internal wall seconds. Original portable SOURCE limits were500 total/450 tree wall checkpoints and observed2GiB RSS, under its separately funded owner. These are patterns only; a new package must prospectively freeze its own sufficient inclusive CPU/wall/RSS/read/publication/cleanup allowance and never claim the old allowance funds this work.

Guard lexical numeric syntax before Fraction conversion in any new adapter. Duplicate/nonfinite JSON rejects. The target/native-number distinction and avoiding opaque diagnostic traversal are new interface qualification targets; successful old predicate checks must not be rerun as an extra preliminary audit. One fresh exported CLI invocation should perform the newly authorized complete retained check, with no second in-process full verification afterward.

## Precisely scoped portable claim and next step

Minimal bundle claim: independently check the sign for the explicitly supplied rational-consumption DECLARED descriptor, with source-bound identity to the closed target semantics. Source-to-exact-law transformation and broader paired-arc canonical dominance remain linked to the closed admission/proof, not secretly requalified. A fully independent raw-source transformation/OD/access audit would require additional projected source inputs and is NOT needed or proposed in this minimal phase. Empirical road realization remains unknown.

The source/API seams are now resolved. A small new CLI/assembler is justified; no native/recovery/worker stage dependency remains. Parent can separately choose source owners, schemas, controls, pins, command and inclusive funding, then review/freeze before one portability qualification. Default remains local author review, license/redistribution unresolved, author-run verification NOT external replication. No manifest, implementation, export or dispatch was created by this task.
