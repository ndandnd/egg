# Independent public Sistig intake preflight — 2026-09-27

**Verdict: PASS for the pinned public input and finite-graph transformation, with the scope limits below.** No blocking source-arithmetic, directed-movement, waiting-energy, depot-restriction, time-precision or provenance defect was found. No optimizer, cluster operation, or author-source edit was performed. This reviewer did not author the Sistig adapter. The native physical model was authored by this reviewer earlier, so this note does not replace the separate independent native-model audit.

## Evidence and independence

`check_source.py` in this directory reads the original ZIP with `zipfile`, original XLSX rows with `openpyxl`, and the original MAT object with `scipy.io.loadmat`. It does not import the adapter or native physical code; a meta-path guard rejects `mip` and `gurobipy`. It independently reconstructs the finite movement graph, energy arithmetic, and a simple existence witness. `source-check.json` records the checked derived-input hash and 52,874 assertions (many are parallel field comparisons, not independent statistical trials). Running the script writes only its own review JSON.

The original archive SHA-256 is `3c6c2ed7c45fc441f4cb6108d830769b60c0de5e44e1a3a6fc72bed4f5f07317`. Local Figshare v1 metadata independently records the same title/DOI, archive size 267,312,231 bytes, MD5 `89b04ee5e8cd54997df51211d2c264d2`, and CC BY 4.0 license. All six recorded member hashes, CRCs and sizes match original bytes. No archive contents were copied into this review directory.

Final reviewed files (SHA-256):

| File | SHA-256 |
|---|---|
| Adapter | `f47a7a926d102f948d73e6d450f25a46fe7ad84fc93e4ff7e877da76ffe0e3c9` |
| Adapter tests | `367f1560c19a1f7d93fe2f4cda0700e95608ca120da2a2bc4b34dea26a717a2d` |
| Public-case protocol | `f807cc71d106e8ab1b3a558098a84ef996800d796047fff58d418b33701626ce` |
| Derived JSON | `af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6` |
| Attribution | `96810c5e6a30eaa390a5b919de15fe40e02fad4d2072740d72779e816786722c` |

## Source and physical translation findings

- The original four parsed workbooks have 37 service rows, five stop rows, three itinerary rows and two route rows, with no blank rows between records. All 785 original field values and recorded physical row numbers match the derived artifact. All trip itinerary/route/endpoints/distances/heights and stop counts reconcile. An additional direct ZIP/XML row count of all 20 selected-operator trip workbooks confirms this is the smallest complete timetable (37; next smallest 105).
- All timestamp strings reconcile with source integer seconds and service duration; the latest arrival is 87,840 seconds, or 24:24. Native conversion preserves the day offset. All 25 original directed time/distance/elevation cells match exactly, in source stop order. Fifteen off-diagonal travel times require half-minute precision. The elevation array agrees with destination elevation minus origin elevation, providing a separate consistency check on the row-origin/column-destination interpretation; no reverse arc is synthesized.
- Independent enumeration matches **every one of 2,705 modes and 5,226 legs** across both variants. Depot 15 has 37 pullouts, 37 pullins, 666 direct modes and 630 depot detours. Depot 16 has the same pullouts/pullins/directs and 595 depot detours. All fixed leg endpoints and times match exactly; all modeled energy values and source provenance agree within a relative `1e-10` arithmetic comparison tolerance.
- The direct-wait question is resolved for this exact input: all service endpoints are stops 6, 7 or 13, whose source depot flags are false. Neither source depot 15 nor 16 is a service endpoint. Thus each variant has 648 positive off-depot waits and 18 exact-arrival direct modes, with zero direct waits at either depot. The author added a fail-closed check rather than silently generalizing this classification to another dataset.
- Service energy uses 1.2 kWh/km plus 16 kWh/h during service. Directed travel energy uses 0.96 kWh/km plus 16 kWh/h during the source travel duration. An early direct arrival has an explicit zero-distance waiting leg with 16 kWh/h; depot-detour idle time has no auxiliary load by the stated scenario policy. Distances are converted metres→kilometres exactly where required. These are modeled assumptions and are consistently separated from absent source energy observations.
- Every emitted pullout, depot detour and pullin uses the selected source depot. The other source depot never becomes a charging or parking option in that variant. Keeping the two variants separate is necessary; neither is the original two-depot source optimization problem.

The primary article's Methods were fetched independently and support the description of DELFI-derived, curated timetables, estimated missing distances, directed routing-based deadheads, and a depot-charging study. [Primary article](https://www.nature.com/articles/s44333-025-00030-y). The article also distinguishes usable battery capacity from installed capacity and discusses four-output overnight infrastructure. The numerical Table 2 endpoint and PDF endpoint were unavailable to this reviewer; the specific EB-3 numeric attribution remains dependent on the author's primary-table transcription. This does not affect the independent arithmetic checks of the explicitly declared rates. It should not be described as an independent second transcription of Table 2.

## Constructive witness and admission limits

Using only original service/matrix rows and the declared rates, this reviewer independently formed 37 one-service bus paths, each with its exact directed pullout and pullin. Every path's energy is below 400 kWh. Sorting their depot-return releases and charging them serially at 360 kW yields:

| Variant depot | Total replenishment, kWh | Final charge end, minutes | Deadline, minutes |
|---|---:|---:|---:|
| 15 | 2089.8764409985934 | 1490.5238145685698 | 1800 |
| 16 | 2769.8144794193895 | 1501.1225345685698 | 1800 |

These agree with the adapter's constructive-replay summaries within ordinary floating arithmetic. The existence construction is independent of an optimizer, but it is only a 37-bus feasible witness under the declared model: it says nothing about fleet minima, certified pricing, hull values, cost savings, or real operations. The witness aggregate was independently recomputed; this source review did not repeat the separate physical solver/replay audit.

No remaining issue blocks freezing the derived input for bounded software qualification. Before an operational scientific campaign, preserve the separate choices already documented: one-depot restriction, fixed departure menu, 30-hour deadline, reserve zero, efficiency one, homogeneous connector, modeled EB-3 rates, synthetic fleet cost, and no driver/crew/TCO model. The source feed's original terms and missing calendar date remain provenance limits, not facts repaired by the adapter.

The vehicle-indexed formulation's candidate charge-variable counts (751,914 and 705,294) are a practical admission concern, not an input defect. A compact formulation preserving all services and the complete declared graph is preferable to silently truncating the timetable. No solve should be inferred from these dimension counts.
