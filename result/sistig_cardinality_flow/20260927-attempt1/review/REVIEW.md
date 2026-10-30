# Independent post-run audit: Sistig cardinality flow

**Verdict: PASS.** I independently reconstructed both frozen 37-service networks from JSON using only Python's standard library and exact fractions. I did not import or call the flow algorithm, its certificate verifier, the flat-energy relaxation, the author runner, or an optimizer.

The sealed archive contains nine files; every recorded byte count and SHA-256 matches MANIFEST.json. STARTED.json, the supervisor launch, summary, frozen input, and receipt agree on the frozen-input digest. The receipt records child and supervisor exit code 0, no timeout or exception, 0.56945 seconds under the 150-second cap, unchanged source pins, and the summary records exactly two algorithm calls and no optimizer invocation. All 17 pinned source files match both the live files and their Git blobs at frozen commit dd5ad1659248b93d53f7f1515282d9530343567f. The working checkout is now at a later backup commit, 5d7f2563; the pinned blobs and live files still match.

The public payload SHA-256 is af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6. For both depot identities I matched all 37 trip records and all frozen movement records to the corresponding public payload case. The exact binary representation of the stored flat price is 3602879701896397/18014398509481984.

For each case I rebuilt the baseline from service energy, 37 vehicle charges, and the least-cost declared pullout and pullin for each service. I then rebuilt all 37 source arcs, all 37 unmatched arcs, the real successor arcs, all 37 unit-capacity successor columns, and the 35-unit gate. Each real arc uses the least exact cost across both direct and depot connection modes, breaking equal costs by movement ID. Every arc endpoint, capacity, and exact rational cost matches the certificate.

The residual certificate passes in both cases: all 37 units satisfy the required node balances; all available forward and reverse residual arcs have the correct reduced-cost signs; the sink potential is zero; and the exact network primal equals the residual-potential dual value. Adding the independently reconstructed baseline reproduces each published fraction. Decoding the flow reproduces the listed movement IDs and direct movement objective. Each certificate uses 35 real connections, two unmatched rows, two unused columns, and 39 selected movement IDs.

A concrete parallel-mode check is real:0:4 in depot 15, connecting H0002 to H0018. The two stored modes are depot_D15_H0002_H0018 at 4428672317382773723068709877597/633825300114114700748351602688 and direct_H0002_H0018 at 42009857597296549445223932177387/5070602400912917605986812821504. The depot mode is cheaper. Subtracting the independently reconstructed cheapest pullin for H0002, cheapest pullout for H0018, and vehicle cost 100 yields exactly -100, matching the saved real arc. The audit also deliberately reruns reconstruction with depot modes omitted and confirms that this mistake is rejected.

The first draft of this independent reviewer included only direct modes and therefore reported false cost mismatches. The protocol's reduction applies to declared connection modes, and the frozen payload contains depot successor modes as well. After including both mode kinds, every saved cost matches the complete exact reconstruction. This was a reviewer-code omission; no source or raw archive file was changed.

| Depot | New cardinality-gated exact ideal stored-input lower bound | Prior V1 matching lower bound | Tolerance-qualified two-bus native numerical upper witness |
|---|---:|---:|---:|
| 15 | 4106419645886056876377559228024553/10141204801825835211973625643008 (404.924239883878) | 1527850306129491653603056061110569/5070602400912917605986812821504 (301.315343883878) | 408.5331368838794 |
| 16 | 131326849408614023975031142206669/316912650057057350374175801344 (414.394469217211) | 1549747520056147657492789450008273/5070602400912917605986812821504 (305.633807883878) | 433.74608621721006 |

The archived V1 matching audit passed and its raw nine-file manifest verifies. Its one-path lower bounds are shown as a comparison between stored-input relaxations. The native upper witnesses come from the separate numerical audit and remain tolerance-qualified. They are listed as separate evidence; this review does not subtract them from the exact bounds or assert a physical optimum or physical gap.

Six certificate corruptions per case were rejected: deleting an arc, changing capacity, breaking gate flow, changing a potential, changing the network objective, and changing the published bound. The direct-only reconstruction omission was also rejected for each case.

The full machine-readable checks and exact witness values are in audit-report.json; the independent verifier is independent_cardinality_audit.py. The verifier uses only standard-library modules and writes only within this new review directory.
