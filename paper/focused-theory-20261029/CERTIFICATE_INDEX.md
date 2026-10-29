# Public certificate index for an external reader

This is a navigation and verification specification for retained evidence. A local standalone command has now passed; it is not a public distribution or external replication. All paths are relative to the repository root `ml-prediction-20261017`. Revisions below are immutable Git objects; source and result revisions are deliberately distinguished. This index is maintained from approved compact maps/results and narrow source entry points, without independently opening compressed evidence or rerunning an audit.

## What model is certified

The case is the descriptor at revision `253c1e29295e766b3889fc8f5c28d9808e00b3d6`, path `research-20261029/public_support_resolution/attempt01/case_descriptor.json`, identity `1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7`.

It admits exactly its finite declared movement modes, fixed leg times/energies, fleet cap and charging-access windows. Charging remains continuous. One bus corresponds to a service-covering path with full initial/final inventory; there is no V2G. The complete directed movement-data matrix does not admit arbitrary unlisted routes, retiming or extra charging access. `MODEL_TO_CERTIFICATE_REVIEW.md` proves the physical-to-row inclusion for this declared set and explains that material limitation.

Supply uses 30 market intervals and original stored-binary coefficients

    a = 3602879701896397/18014398509481984,
    b = 5124095576030431/4611686018427387904,
    F(e) = Σ(a e_t + b e_t²/2).

The perspective energy-flow and independent reconstruction sources are pinned at `3278d50f8323618bd36809b1bbb1a0da081e23ff`: `research-20261029/public_support_resolution/energy_flow.py`, `exact_dual.py`, and required `src/egglab/native_recharge.py`/package schema. Every lower refers to that rational semantic model, not an unqualified native floating-point objective.

## Original sign certificate and retained evidence

This table preserves the original sign-certificate chain. Its physical lower
is denoted L_phys_old in the constants below; the stronger current physical
interval and its distinct endpoint-rounding convention follow the table.

| Claim | Source/input/output binding | Checking entry point and scope |
|---|---|---|
| `D ≤ U_phys`, safely displayed `441.532913` | Rational-recovery producer source `425bf35452eb3f5444f20058ad6fd6b540ffed88`, control `869cae89`; output revision `0cb3c54de6e8e5c391afb37bcbb68ad3a51925ee`, `research-20261029/public_rational_recovery/attempt01/PUBLIC_PRIMAL.json.gz`; transfer authority revision `3cbb8c9d965e9222ef8a98191bf775b4925382a1`, `research-20261029/public_rational_recovery/TRANSFER_AUTHORITY.json` | Original physical replay `independent_verify.verify(case_dict,candidate)` checks service/path coverage, exact inventory/charging and loads. `PUBLIC_DUAL.json.gz` additionally supplies a fixed-topology optimum certificate checked by `recovery.check_certificate`; that conditional lower is not global D or CH. |
| `CH ≤ U_hull`, safely displayed `441.142238` | Price-witness source `cddd5072be949c36a8f674dd12298503a73407a7`, control `61b14412`; output revision `f5ec2aa5770188d173af7297620a5fcea99fef9a`, `research-20261029/public_price_witness/attempt01/MIXTURE.json.gz`, admitted components `transferred_incumbent.json` and `new_physical_response.json`; authority revision `c5f056b90ca895786c44f96903cdaafff97fce52`, `research-20261029/public_price_witness/TRANSFER_AUTHORITY.json` | Producer `worker.check_mixture(left,right,a,b,answer)` checks exact mean load/ops, quadratic value and segment KKT. Component physical admission is separate retained authority. The feasible segment mean is a hull upper, not a dispatch or global hull optimum. |
| `D ≥ L_phys`, downward display `441.151027` | Tree/checker source `6a171357b65254b52cade63ed95dcce798485f36`, control `6bdcf254`; output revision `ef0e08203dba5ac2ddcaff6bd8639cc9a70677b9`, `research-20261029/public_support_tree/attempt01/PUBLIC_TREE.json.gz`, `INDEPENDENT_TREE_CHECK.json.gz`, compact results/receipts | `checker.prepare(case,exact_dual._reconstruct,mode='quadratic',fleet_count=2,case_token=...)`, `verify_node`, `verify_tree`; reference proofs materialized by `producer.materialize_tree`. All 303 nodes cover the exactly-two physical domain. Independently reconstructed minimum-fleet obstruction plus typed physical-three-plus service/fee floor complete global D. Neither restriction applies to arbitrary hull components. |
| `D−CH ≥ L_phys−U_hull > 0`, downward exact-difference display `0.008790` | Same tree compact `attempt01/results.json`, `INDEPENDENT_TREE_CHECK` summary, source-bound hull authority above | Exact rational subtraction and strict comparison, after independently establishing global physical lower and feasible hull upper. Do not subtract rounded six-decimal displays. This proves unsupported physical optima under the manuscript's own-price qualifications, not a strategic-price game or all possible tariffs. |
| `CH ≥ L_root`, retained conservative display `434.17` | Energy-flow producer source `c8ed513e64da7cb2ea478a73b1455e5a760a37c8`, control `b72e6fb0`; closed packet revision `f8a043132863db5ce631d5691d35b5d788bdf256`, `research-20261029/public_energy_flow/attempt01/ROOT_QP.json.gz` | `exact_dual.verify_and_bound(case_dict,result)` checks reconstructed rational rows, objective, finite bounds and tangent/residual certificate. Its unrestricted continuous outer relaxation bounds the complete-plan hull as well as physical D. This scope differs from the branched quadratic physical tree. |

Each package's compact `RESULTS.md`, `attempt01/results.json`, owner/worker receipts and final resource receipt state the acceptance boundary and paid cost. Prior failed physical screens/recoveries are not overwritten by later admitted constructions. Native OPTIMAL alone proves none of the exact inequalities above.

## Refined physical lower and current conservative gap

The later physical-refinement source is `a2156a0cce74cefaa9e457f3e766d952e09f59c5`, control `ba0059ce`, artifact `d8e22ffd3753fced3ec825c68714fd549d914230`. Its compact `research-20261029/public_physical_refinement/attempt01/results.json` records VALID_REFINEMENT, complete base coverage and epsilon_met. All152 source-admitted original frontier identities and inherited decisions remain covered;72 new nodes were checked after102 new native proposals. New `checker.verify_refinements` combines their checked bounds with retained base evidence and the same fleet-count argument. No old303-node algebra audit/search was repeated.

The current outward interval is `441.532912 <= D <= 441.532913`, width at most `0.000001`. Combining its down-rounded lower with retained up-rounded `CH <= 441.142238` gives **conservative endpoint bound `D−CH >= 0.390674`**. This is not an exact-gap display. The table's original `0.008790` remains the historical downward display of its exact rational difference. The refinement supplies no CH lower; neither exact optimum is known.

## Exact accepted constants

These constants are transcribed from approved compact records, not recomputed here:

    U_phys = 15487225773558335836678536516523969405935273717647515
             /35076039295941670036888435985190792471742381031424

    U_hull = 1443179923968803775290098006217163515009032774663398228930303365915411930614170875502024167442451530845
             /3271461678119739162838778949479488288386427183774469641575516104263648171125254058271345771399872512

    L_phys = 80662634237282610902559758444585953851595472957985
             /182687704666362864775460604089535377456991567872

    L_phys_old = 161185737312360042121870470606817314079130382670151
             /365375409332725729550921208179070754913983135744

    L_phys_old−U_hull = 28757315678009341708588197937979967078054123344385860826329513296439211419698507473389021538473603
             /3271461678119739162838778949479488288386427183774469641575516104263648171125254058271345771399872512

    L_root = 89305539793542554823848003373759814314980879303792249486127549713
             /205688069665150755269371147819668813122841983204197482918576128

The separately closed fee-only extension source is `872e38aef22dd4f736daa4862fa46b4d38af811b`, control `d37fea3b`, package `research-20261029/public_fee_stability/attempt01`. Its compact RESULTS and PUBLIC_INTERVAL report fixed mean bus count two and sufficient open region f>fcrit, with no upper endpoint:

    fcrit = 207144809919773459175544589361909362103645314362363582220429474260291397350199127418953716376701502557
            /3271461678119739162838778949479488288386427183774469641575516104263648171125254058271345771399872512.

`checker.check(fields,proposed)` checks exact interval intersection, bound/mixture metadata and openness. Its source-bound affine three-plus floor is essential for negative fee shifts; no generic old bound is shifted by three times the fee change. All f≥100 preserve the nominal positive gap guarantee. The endpoint is not a maximality or support-restoration claim. This index does not invent a fee output-artifact commit; consult the parent closeout for its eventual immutable result revision before external transfer.

## Retained-evidence verification versus search regeneration

An offline reader should first obtain the exact revisions and fixed-path buffers, authenticate the sources/descriptor/authorities and inspect successful complete receipts. Then reconstruct semantic rows independently, check physical upper witnesses, check the two-plan mixture, and verify every retained tree leaf/branch and fleet-count exclusion using rational arithmetic. Finally compare exact constants. This verifies retained evidence without rerunning native search. The tree's original 353 native calls are evidence generation, not a necessary step of its rational leaf-algebra/coverage check. The standard tangent, finite-box residual and Farkas formulas are explained in `certificates.tex`.

Regenerating native proposals is a different, expensive procedure requiring a fresh namespace, independently obtained compatible Gurobi environment, complete acquisition/admission/search/check/publication accounting and prospectively fixed resources. A closed attempt directory must not be resubmitted. Native timing, bases and floating solutions need not reproduce bit-for-bit for the retained exact proof to remain valid.

## Local standalone verification and remaining external gap

`research-20261029/public_certificate_bundle/attempt01` is CLOSED_PASS from source `f6845fe6d803607a88d05e6b3284fd53bb4eb58d` and separate control `1ad59047`. Its exported `public-sign-verifier` directory contains the six exact evidence packets, three immutable independent checker sources, new adapter and manifest. A single fresh isolated POSIX CPython process passed all375 combined tree nodes, both full physical points, the fixed mixture and freshly reconstructed fleet exclusions. It reproduced L_phys above with zero native calls. Full local construction/check cost32.62 displayedCPU/33.26elapsed; peak observedRSS659914752bytes. See the package's compact RESULTS, verification.json and FINAL_RESOURCE_RECEIPT.

The manifest must be authenticated through a separate trusted channel. For this admitted local export its digest is `fa7d7d40c95e185eb4165fe2cb19e14ca0e5cbf63db0321b0c7d4bc5c007c6e7`. From an untouched authorized copy, the reader-facing command is:

```sh
python3 -I -S -B verify.py --manifest-sha256 fa7d7d40c95e185eb4165fe2cb19e14ca0e5cbf63db0321b0c7d4bc5c007c6e7 --output verification.json
```

It requires POSIX CPython stdlib, no site packages, Git, network or optimizer. Output creation is exclusive: the closed author's copy already has its output and must not be rerun. The builder requires Git to assemble pinned inputs; the exported check does not. Constructing the bundle and checking exported-copy integrity are separately paid trust stages, not repeated native discovery. The local adapter Q0 comprises2 anchors and13 negative controls.

**External replication and redistribution remain unresolved.** The successful invocation was author-run on the same host. The generated bundle stays local while source/data licensing and release rights are reviewed; only compact provenance/results and new source are backed up. No third-party/platform validation or published verification distribution is claimed. Internal independent mathematical checking and a fresh exported command strengthen reproducibility but do not substitute for external scrutiny.
