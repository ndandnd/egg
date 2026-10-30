# Manuscript v0.5 final acceptance review

**Verdict: PASS for author/user review; not journal-submission clearance.** All 27 pages of the final review-candidate PDF were rendered and inspected. After the abstract correction, pages 1–6 were rendered and checked again; page count remains 27 and extracted page text changes only on pages 1–6. The remaining pages, figures and tables match the inspected candidate. No clipping, overlaps, broken page numbers, or illegible math, captions or tables were found. The 18 external DOI/arXiv link annotations are readable and well formed.

## Scientific and display checks

- The abstract now distinguishes the exact ideal depot-15 results from the off-protocol numerical diagnostic; it says the public gap remains unresolved and limits positive regret to a bounded planner incumbent, not a proven optimum.
- Section 8 and Table 5 keep the numerical reconstruction separate from protocol compliance. The 5.190904918592423 s hull-polishing time against the frozen 5.0 s cap is prominent in text, Table 4, Figure 8 and the evidence map. The manuscript makes no protocol-pass, positive public-gap, optimal-fleet regret, or operational claim.
- Table 4's five six-decimal intervals round outward from the independently reconstructed exact stored-float endpoints: planner, hull, own-price response, signed gap and incumbent regret. The hull remains `budget_exhausted`; the own-price response status is stage-specific.
- Figure 8 clearly labels the mixture mean as non-executable, the gap as unresolved at five, and regret as named-incumbent-only. Table 2/3 and Figure 7 preserve the original flat-price numerical results; depot 15's exact minimum fleet and ideal bounds remain distinct from depot 16's numerical upper witness.
- The earlier physical-assumption clarity issue is resolved by the Section 8 input table, which states service/deadhead energy rates, zero reserve, unit efficiency, shared/per-bus power, full SOC restoration and the finite 30:00 boundary. These remain declared synthetic assumptions, not telemetry or recurring-daily feasibility.

The full independent numerical audit is pinned at SHA-256 `dc1b176371cd5295d9bfcfd562b7cb69aaa8c3026c5c3a344a023d83a8027598`. Its verdict is numerical-evidence audit PASS, protocol compliance FAIL, and no overall PASS. The candidate is suitable for user review; final submission still requires journal-specific styling and any later editorial decisions. No source, manuscript, figure, PDF, result, or Git change was made during this review.
