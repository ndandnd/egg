# Next-revision evidence insertions — 27 September 2026

Draft only for the next bundled manuscript revision. Do not edit `manuscript.md`, rebuild the PDF, or change Figure 7 during this insertion pass. Preserve Table 2's original flat-price intervals exactly. The nonlinear public pilot has not run; GRB hull qualification is pending.

## 1. Replace the Table 2 caption paragraph

**Target:** immediately below the two unchanged Table 2 data rows.

```text
Table 2. Complete public flat-price pilot under synthetic costs. These are the original conditional native numerical intervals; neither proves cost optimality. The exact stored-input one-bus obstruction proves fleet cardinality at least two for these graphs. Separately audited, tolerance-qualified two-bus witnesses are consistent with that lower bound, but do not provide an exact minimum-fleet certificate or establish cost optimality. The 37-bus references remain feasibility constructions, not an operational savings baseline.
```

## 2. Replace the post-pilot diagnostic tail

**Target:** replace only the text beginning “An independently audited post-pilot diagnostic…” through the end of that paragraph. Leave the preceding first-pilot audit, timing, archive and failed-attempt history intact.

```text
An independently reviewed exact stored-input obstruction rules out a one-bus cover in both full 37-service graphs. All mandatory services consume 889.117519 kWh against 400 kWh usable inventory, and each of the 36 chronologically forced interservice transitions has only a direct mode, so no modeled depot recharge can occur along a one-bus cover; service plus forced-leg energy is 980.317519 kWh. This proves a fleet-cardinality lower bound of two for the declared graphs. The separately audited two-bus witnesses are consistent with this lower bound under the declared numerical feasibility policy, but are tolerance-qualified and do not provide an exact minimum-fleet certificate or cost-optimality proof ([independent one-bus review](../research-20260927/agent-notes/sistig-one-bus-postpilot-review/REVIEW.md)).

Two separately audited exact stored-input relaxations give lower bounds for the flat-price objective. The earlier one-path matching relaxation gives 301.315343883878 for depot 15 and 305.633807883878 for depot 16; the later cardinality-flow relaxation strengthens these to 404.924239883878 and 414.394469217211 ([cardinality-flow review](../result/sistig_cardinality_flow/20260927-attempt1/review/REVIEW.md)). The separate native two-bus upper witnesses are 408.5331368838794 and 433.74608621721006; these are tolerance-qualified physical replays, not exact rational witnesses ([physical result audit](../result/sistig_pricing/20260927-grb-job557543-attempt1/review/REVIEW.md)). Keep both ideal lower bounds and numerical upper witnesses distinct from the original Table 2 intervals. They establish neither an exact physical optimum nor an exact physical optimality gap. The exact matching and cardinality-flow relaxations are not native-matrix lower-bound certificates.
```

## 3. Insert a qualification update in Appendix C

**Target:** after the paragraph ending “convex-hull machinery and the public timetable remained separate qualification gates.”

```text
Subsequent independently audited compact V3 qualifications pass their declared synthetic controls. CBC physical attempt 3 passed 20/20 (16 certificates, four expected infeasibilities) in 35 calls; its audit reconstructed 589 raw variables and 31 physical witnesses and rejected 25 corruptions. A separate GRB physical qualification passed 20/20 (16 certificates, four expected infeasibilities) in 35 calls, with 31 witnesses and 26 corruptions rejected. The CBC V3 hull attempt 2 passed 8/8, with 21 pricing calls, 15 master calls and 48 corruptions rejected ([CBC physical review](../result/native_pathflow/20260927-attempt3/review/REVIEW.md); [GRB physical audit](../doc/NATIVE_V3_GRB_PHYSICAL_RESULT_AUDIT_20260927.md); [CBC hull review](../result/native_pathflow_hull/20260927-attempt2/review/REVIEW.md)). These are separate small synthetic fixture qualifications, not a solver-performance comparison. GRB hull qualification and the nonlinear public physical-versus-hull pilot remain pending.
```

## 4. Replace two Table 3 evidence-map rows

```markdown
| Does the compact native implementation pass its fixture controls? | Independent CBC V3 physical attempt-3, GRB physical, and CBC V3 hull result audits | CBC and GRB physical: 20/20 each (16 certificates, four expected infeasibilities); CBC hull: 8/8. The earlier energy-band V2 attempt-2 failure remains preserved. Synthetic qualification only; GRB hull and nonlinear public pilot remain pending. No solver-performance comparison. |
| What is known for the full public timetable? | Original flat-price intervals; exact one-bus obstruction; one-path matching and cardinality-flow relaxations; separate numerical two-bus witnesses | The exact obstruction proves fleet cardinality at least two for each declared graph. The two-bus witnesses are separate tolerance-qualified feasibility results, consistent with but not an exact minimum-fleet certificate. Ideal stored-input lower bounds: 404.924239883878 / 414.394469217211; earlier matching bounds: 301.315343883878 / 305.633807883878. Numerical upper witnesses: 408.5331368838794 / 433.74608621721006. No exact physical optimum or gap; nonlinear gap and regret remain open. |
```

The old Table 2 values, the first flat-price pilot's wide intervals, and Figure 7 remain unchanged. The new evidence improves the ideal stored-input lower bounds, proves the ideal one-bus obstruction, and separately records tolerance-qualified two-bus witnesses; it does not establish a physical cost optimum, a physical optimality gap, operational benefit, or backend superiority.
