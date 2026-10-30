# Theory and exact-result source map

This map supports the four LaTeX files `model_theory.tex`, `exact_results.tex`,
`public_case.tex`, and `proof_appendix.tex`. It records the existing source of
each mathematical or numerical statement; no new optimization was run.

| Draft material | Existing source and scope |
|---|---|
| Common complete-fleet set, compactness, planner/hull definitions, own-price regret, price-support inequality and converse | `paper/manuscript.md` §§3–4 (historical v0.5). Appendix proof in the new TeX restates that derivation. The general convexification context is attributed through existing BibTeX keys `starr1969`, `oneill2005`, `gribikHoganPope2007`, `huaBaldick2017`, and `schiro2016`; no novel general theorem is claimed. |
| Fleet and supplier LOC identity; distinct own and hull prices; quadratic upper regret bound | `paper/manuscript.md` §4. The upper bound uses the physical load diameter in the quadratic seminorm. The new proof makes compactness and hull first-order optimality explicit. |
| Complete physical path, energy, charging, serial connector assumptions and dual bound directions | `paper/manuscript.md` §4.1 and Appendix A. The new TeX is a lean mathematical description, not a solver formulation or a certification claim for all instances. |
| Two-service physical branches, objective values `D=97`, `CH=7591/80`, gap `169/80`, mixture `27/40`, own-price regret `13`, hull-price fleet LOC `0`, supply LOC `169/80` | `paper/manuscript.md` §5. Exact arithmetic and complete branch argument are repeated in the new appendix. Figure source: `paper/figures/cyclic_gap_and_prices.pdf`. |
| Reserve/loss/single-terminal-connector variant, interval definitions, exact gap `94249/28880`, and strict positive-gap neighborhood | `paper/manuscript.md` §6.1 and Appendix B; independently reviewed scope summarized in `paper/CLAIM_EVIDENCE_LEDGER.md` under the robustness claims. The new appendix reproduces the sufficient inequalities and does not extend them to taper, switching time, or other charger types. |
| Replication `CH_n=7591n/80`, `Δ_n=20δ²/n≤5/n`, subsequence whole-operator regret `351/40+169/(40n)`, ties and reserved-pair bound `20/n` | `paper/manuscript.md` §6.2 and the replication paragraphs of `paper/CLAIM_EVIDENCE_LEDGER.md`. Figure source: `paper/figures/cyclic_replication.pdf`. The exact family assumes demand, connector counts, and supply capacity scale together; participant statements use independently reserved connector rights. |
| Public 37-service Hildenbrand timetable, two separate one-depot cases, modeled energy/charger assumptions and original flat-price pilot intervals | `paper/manuscript.md` §8 and its Tables 2–3. These are declared EGG assumptions and tolerance-qualified numerical results, not measured battery energy or source-network cost optima. |
| One-bus obstruction, exact cardinality-flow lower bounds, exact depot-15 two-bus witness and flat-cost enclosure | `paper/manuscript.md` §8; `doc/SISTIG_EXACT_PUBLIC_WITNESS_ADMISSION_20260927.md`; `paper/CLAIM_EVIDENCE_LEDGER.md` “Newly audited compact and public-case evidence.” Depot 15 has an exact two-bus minimum and ideal flat-cost interval `[404.924239883878…,408.533135883878…]`. Depot 16 has an exact at-least-two obstruction and numerical two-bus witness. |
| Depot-15 ideal nonlinear enclosure `424.365880667204…≤CH≤D≤512.7694256264009…` | `doc/SISTIG_EXACT_NONLINEAR_ENCLOSURE_20260927.md` and `paper/manuscript.md` §8. These are exact rational bounds displayed as decimals for the declared stored-input model. They do not resolve a positive public gap or a public optimum. |

The public manuscript section intentionally omits the off-protocol nonlinear
diagnostic as a headline. Historical v0.5 and `paper/CLAIM_EVIDENCE_LEDGER.md`
identify it as secondary; its signed gap interval crosses zero. The existing
reviewed six-page `computational_results.tex` independently covers development
campaigns, complete-fleet hull bounds, and pricing starts, so the new theory
files do not repeat its tables or timing claims.

## Completed narrow reconciliation

`FLAT_ROUND0_RECONCILIATION.md`, `FLAT_ROUND0_SUMMARY.json` and independent
`FLAT_ROUND0_REVIEW.md` now establish that attempt 2 round 0 is the same
intended depot-15 physical case with the flat linear objective. Its native
numerical optimum is approximately 408.53, subject to native tolerances.
The exact ideal flat enclosure remains [404.92,408.54] after outward rounding;
no exact ideal equality or experiment reclassification is inferred. The earlier
over-cap planner attempt 1 is a different attempt and is not the basis of this
clarification. Exact nonlinear bounds also imply 0 <= D-CH <= 88.41.

The public witness figure reuses `paper/figures/public_pilot_witnesses.pdf`,
whose original source/provenance and layout review are recorded in
`paper/make_public_pilot_figure.py` and
`paper/PUBLIC_PILOT_FIGURE_REVIEW_20260927.md`. Its caption identifies the
original numerical flat-pilot schedules, not the separate exact witness.
