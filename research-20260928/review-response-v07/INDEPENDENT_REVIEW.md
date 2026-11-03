# Independent review of v0.7 manuscript changes

Scope: read-only review of `paper/latex/main.tex`, `model_theory.tex`, `development_supplement.tex`, `computational_support.tex`, and generated `joint_support_table.tex` against the supplied Claude review and finalized `analytic-bounds/DERIVATION.md` / `bounds.json`. I checked claim scope, stated inequalities, cardinality conditions, and reported arithmetic; I did not re-derive the paper's theorems or audit raw solver output.

## Review result

No actionable blocking issue remains in the reviewed manuscript material. The title's full-replenishment qualifier matches the central construction. The abstract distinguishes the exact mechanism from the timetable evidence: it says public intervals do not establish a positive gap and limits positive regret to a returned incumbent, not an unknown optimum. The body keeps price-taking support separate from strategic price anticipation, and does not equate own-price regret with uplift or settlement.

The computational-support section responds to the review's main concern by reporting physical cost, hull cost, gap, and returned-incumbent regret together for the four changed-market cases. Exact public floors are separate from native screen bounds; the mixed-evidence caps are conditional and are not described as timed improvements. The manuscript states that public gap lower endpoints remain zero, public regret is at a time-limited returned incumbent, and the multivisit Fenchel improvement is postprocessing rather than measured acceleration. The historical supplement preserves the capped reuse, failed no-incumbent cells, single-seed start pilot, and distinct campaigns with appropriate limitations. The earlier damping study is deferred in the response record because it used a different terminal rule; the manuscript makes no convergence or hull-algorithm-necessity claim.

The analytical floors match the derivation/JSON after outward rounding: 424.36/418.96 at depot 15 and 435.67/430.27 at depot 16 for markets 0/1. Uniform test prices exceed 0.22; three-plus-bus margins are 67.76 and 56.17. The Fenchel bound direction and fleet-cardinality comparison state the needed conditions: one-bus obstruction, full replenishment, unit efficiency, zero monetary travel cost, nonnegative movement energy, and `p >= max_t a_{s,t}`. Later changed-market lower endpoints 405.83/420.45 and their differences from the floors, 13.13/9.82, match the separate-campaign figures. That comparison is explicitly separate and makes no runtime or exact native-model certificate claim.

The generated table matches the JSON's `native_combined` outward intervals for all four changed-market cases: cyclic gap [1.01, 1.02], multivisit gap [0.00, 0.10], and public gaps [0.00, 177.98] and [0.00, 170.22]. Regret intervals also match. The response-Fenchel lower bound, a physical upper witness as a hull upper, and `D >= CH` are applied in the valid directions. The public native table remains separate from the mixed ideal-floor caps [0.00, 98.37] and [0.00, 117.61]. Native feasibility/replay qualifications remain clear; the saved own-price vector is described as rounded, and exact arithmetic on it is not presented as an ideal real-gradient certificate. Public optimum regret and a positive public gap remain unresolved.

The no-incumbent repair now has a source-map pointer in `REVIEW_RESPONSE.md` to `../no-plan-repair/README.md`; I did not inspect or rerun those tests. The malformed Hümbs author accent in the BibTeX entry was corrected to the proper TeX form.

Root reports a clean 17-page main PDF and 7-page supplement with visual inspection; I did not repeat render QA. No experiments, solver runs, or raw-log review were performed. The historical `paper/latex/computational_results.tex` remains byte-identical to the requested SHA-256.

## Current hashes

- `paper/latex/main.tex`: `92e81402f1da76fc7ce4dc5697290a432863435b525210bb2f7e9d3a8f2e0568`
- `paper/latex/model_theory.tex`: `2ff8164e45f5588451e8f01cc56f99196ba424e1f5a0646b8b0744c5a4a06c2a`
- `paper/latex/development_supplement.tex`: `9322178c48ea1d06b8e4848933ba9198c27a54d54af3ad1674b78217532938dd`
- `paper/latex/computational_support.tex`: `fb720b02995308e197f3009abce92aad5f169c380f5404312026cdd9e4ba9c27`
- `paper/latex/joint_support_table.tex`: `c999609283f8ac35c58f3a0e3d67df446728c42861b6b64ed956372b483152a2`
- `paper/latex/references.bib`: `4467e8c9e6c8f7c5647f392f422bbfc53aabebbea9268674f99108710957363d`
- `paper/latex/computational_results.tex`: `50fda5437632c7286bff016df8c688e7d9a0e5b54896393e271d62834913ffdb`
- `research-20260928/review-response-v07/analytic-bounds/DERIVATION.md`: `77b6d4f582ffa51cf0e5a80d1f6009ea7e0ed86a5cbeed2a0aeb7876e45d61d6`
- `research-20260928/review-response-v07/analytic-bounds/bounds.json`: `681078219cffca0f1bd479220601fc6b8a494d9ef21addc35c4d689965d484e6`
- `research-20260928/review-response-v07/REVIEW_RESPONSE.md`: `3423b13dbe82733ead3c6acebd88432bec452f9e115f2bda2bf780fe7b9a7692`
