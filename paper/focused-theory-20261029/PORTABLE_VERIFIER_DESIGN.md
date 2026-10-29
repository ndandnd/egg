# Minimal solver-free public-sign verifier: portability assessment

Source-only assessment using CERTIFICATE_INDEX, compact approved maps/results and narrow checker imports/writer schemas. No raw evidence, re-audit, execution, imports, tests, hashes or bundle generation occurred. **A small standalone retained-evidence verifier is justified and appears feasible. It does not yet exist.** Authoring and qualifying it would be new separately frozen work, not external replication.

## Smallest scientific closure

For the positive sign alone, retain the declared case, two complete rational physical candidates, their fixed mixture and the full physical tree. Do not include native discovery or optimization sources, saved QP proposals, fixed-route duals or root-relaxation certificates: none is necessary to prove a feasible CH upper below a global physical lower.

Required fixed evidence is:

1. Descriptor at `253c1e29295e766b3889fc8f5c28d9808e00b3d6`, `research-20261029/public_support_resolution/attempt01/case_descriptor.json`.
2. First physical candidate from `recovery.candidate` in `public_rational_recovery/attempt01/PUBLIC_PRIMAL.json.gz`, artifact `0cb3c54de6e8e5c391afb37bcbb68ad3a51925ee`.
3. Second physical candidate from `recovery.candidate` in `public_price_witness/attempt01/EXACT_PRIMAL.json.gz`, artifact `f5ec2aa5770188d173af7297620a5fcea99fef9a`.
4. `public_price_witness/attempt01/MIXTURE.json.gz` at that same artifact revision, providing fixed weights/mean load/ops/value.
5. `public_support_tree/attempt01/PUBLIC_TREE.json.gz` at `ef0e08203dba5ac2ddcaff6bd8639cc9a70677b9`, containing complete branch structure and retained proof store.

All public_* paths in items 2–5 are under research-20261029. The plain `new_physical_response.json` does **not** contain selected routes/charges; it is insufficient for independent physical replay. The full EXACT_PRIMAL packet is necessary unless a separately admitted compact extraction preserves its complete candidate. No omitted-plan admission may be replaced by trusting a stored “ADMITTED” boolean.

Checking sources are stdlib-only: `independent_verify.py` and `exact_dual.py` at semantic revision `3278d50f8323618bd36809b1bbb1a0da081e23ff`, and `public_support_tree/checker.py` at `6a171357b65254b52cade63ed95dcce798485f36`. Inspection confirms these modules import only collections/Fraction/time and receive plain dictionaries. No native_recharge, energy_flow, Gurobi, mip or proprietary license is needed for this checking closure. A small new adapter must expand retained proof references without importing producer/search code.

## Exact verification sequence

Authenticate fixed manifest bytes before decoding. Reconstruct the exact declared model and coefficient semantics, not a serialized alleged constraint context. Preserve original JSON numeric-to-binary-float semantics for descriptor values before Fraction conversion; parsing floats as decimal rationals would silently change the model. Reject nonfinite/duplicate-key/malformed inputs and enforce explicit file/decompressed-size limits.

Call `independent_verify.verify(case_dict,candidate)` separately for both complete candidates. Require strict physical pass and no repairs/tolerances, reconstruct their loads/ops/objectives, and compare any reported values. The candidates include all selected movement IDs and interval charge cells, so service coverage, inventories, connector use and full refill can be rechecked independently. Fixed-topology optimality is unnecessary for these upper witnesses.

Read fixed mixture weights, require complementary weights in [0,1], independently form mean loads/ops from the two newly replayed candidates and evaluate the original rational quadratic supply cost. This establishes a CH upper without a mixture KKT test or reoptimization: any feasible mixture suffices. Require agreement with the retained mixture fields and accepted U_hull. Do not require historical source-authority booleans in place of physical verification.

Construct `checker.prepare(case_dict,exact_dual._reconstruct,mode='quadratic',fleet_count=2,case_token=...)`. Materialize only canonical certificate vectors named by each retained proof reference. Ignore native status, solver bounds, producer `verified` flags and node search labels as proof authority. Run `checker.verify_tree` with explicit node/depth/operation/fraction/time limits; require COMPLETE, both-child coverage and no unknown/open/unreachable/shared nodes.

Independently derive the minimum-fleet obstruction from the fresh semantic reconstruction. Construct the physical-three-plus floor from declared nonnegative vehicle/nonfee costs, consumption, full refill and the original affine supply coefficient, using the checker's typed exclusion algebra. This requires no trusted old exclusion assertion. A local callback may authorize this freshly constructed exact floor only after checking its explicit case/scope conditions; it must not blindly return true on artifact metadata. Combine it with two-bus coverage for global D. Require finite global lower and strict rational D_lower>CH_upper. Print exact fractions and conservative displays as secondary information. Scope remains the pinned finite declared-movement model, not arbitrary unlisted travel/access choices.

## Proposed bundle and command

    public-sign-verifier/
      README.md
      LICENSES/                 # applicable source/data notices, checked first
      MANIFEST.json             # fixed source/input IDs, paths, lengths, digests
      verify.py                 # new thin adapter, no solver or search imports
      checkers/                 # three immutable checking source files
      evidence/                 # five fixed evidence objects listed above
      expected.json             # exact accepted constants and scope, no authority
      qualification.json        # separately produced author-run receipt

Prospective invocation after construction and review:

    python3 -I -S -B verify.py --manifest MANIFEST.json --output verification.json

The executable should work without Git, network, package installation or environment-specific absolute paths. Use an explicitly qualified CPython version (initially the author environment, then a genuinely separate portable environment); do not promise all Python/platform combinations before testing. Stdlib gzip/json/Fraction/time are sufficient computational dependencies. Filenames are manifest-defined fixed bundle members, never followed from certificate contents. Bound decompression, arithmetic and wall/CPU resources; resource exhaustion is UNRESOLVED/nonzero exit, never PASS. A deterministic report distinguishes physical admission, mixture upper, tree coverage, fleet exclusions and final sign.

The unmodified complete packets are the least new trust-sensitive packaging choice, though they include unused native metadata. A compact evidence-only bundle would reduce size but requires a separately frozen extraction mapping and equivalence/admission receipt; it must preserve both full candidates, every proof-referenced vector, complete tree and exact coefficients. Do not strip fields opportunistically after seeing checker failures.

## Qualification, trust and effort

New qualification should test adapter schema/paths, wrong/missing candidate and charge cells, changed service identity, mixture weight/value, missing tree child/proof reference and altered objective/floor/scope. Reuse the already qualified mathematical checker rather than repeat a broad historical qualification suite. One separately funded full retained-evidence check is necessary because this adapter newly replays both plans and checks the tree in a portable closure. That is purposeful new external-readiness work, not a claim that it has already run. The expensive 353-call native search need not be regenerated.

Estimated source effort is a few hundred lines of adapter/manifest/README work, roughly one to three focused authoring hours plus independent review and one bounded qualification. Runtime/resource allowance must be chosen prospectively; previous internal tree-check timing is only planning context, not a portable performance guarantee. Repository distribution rights and availability of the pinned evidence must be checked before publishing the bundle.

An author-written separate verifier and an author-run portable-environment check improve inspectability and portability. **External replication requires an independent person/team to obtain the bundle, execute it and report their result.** Neither this design, the existing internal checks nor a later author-run PASS should be described as that external replication. Present status remains: design only; no runnable bundle, qualified invocation or external run supplied.
