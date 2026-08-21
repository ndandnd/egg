# Candidate research inbox — sweep of 2026-08-20 (noncanonical)

> **Status:** discovery and triage only. This file is a candidate research
> inbox, not canonical literature-review closure, scored evidence, or
> cite-ready prose.
>
> **Provisional sweep result:** No collision found in this sweep, pending
> canonical ingestion, dimensional scoring, and full-text verification.

The discovery sweep ran on 2026-08-20 against the canonical snapshot dated
2026-08-14. Source pinning and the corrections below were checked on
2026-08-21. The sweep was not exhaustive: it did not produce a reproducible
query log, some services rate-limited requests, and most candidate records
remain metadata- or abstract-level.

No candidate in this inbox changes a novelty verdict, establishes an open
niche, or becomes a citation merely by appearing here. Candidate ingestion
and scope decisions belong in a separate cite-and-scope PR. In particular,
this PR intentionally does not modify:

- `ref/papers.csv`;
- `ref/LITERATURE_INDEX.md`;
- `ref/NOVELTY_MATRIX.md`; or
- `ref/READING_QUEUE.md`.

## Canonical baseline: why 322, not the previously reported 323

The canonical baseline is **322 distinct works**. Commit
`e89fdd35d4e1de234a4d1523ad0549624e341fd8` initially reported 323 data rows,
but two rows represented the same work:

- `clp-evsp-csp` with `arXiv 2403.09763`; and
- `clpevspcsp` with `arXiv:2403.09763`.

Commit `f61a3ca8adcfd5d2c6c1f297ccb75793bca7fe24` performed the canonical
deduplication, retained one enriched `clpevspcsp` record, and reduced the
count to 322. The difference is one duplicate representation, not one lost
work. The candidates below have not been ingested, so they do not change that
count.

## Candidate inbox

The descriptions in this section are search-result, metadata, or abstract
triage, not full-paper findings and not canonical dimensional scores.

### Collision and adjacency checks to route through cite-and-scope

- Transportation Research Part C article PII `S0968090X26001968`: inspect
  the bilevel pricing, ride-hailing, and V2G model against Duties, EndogP,
  and Exact.
- Gu and Qin, [arXiv:2510.26036](https://arxiv.org/abs/2510.26036):
  inspect the competitive-equilibrium treatment of spatially flexible
  loads.
- Brenner, Roald, and Amin,
  [arXiv:2510.20805](https://arxiv.org/abs/2510.20805): inspect the strategic
  data-center load and lower-level market model.
- Caustur et al.,
  [arXiv:2509.05940](https://arxiv.org/abs/2509.05940): score the e-bus
  duties, charging cost, and optimality evidence.
- Löbel, Borndörfer, and Weider,
  [arXiv:2407.14446](https://arxiv.org/abs/2407.14446): distinguish
  charging-rate/capacity feedback from endogenous price formation and verify
  the approximation certificates.
- Sun et al., *Energy* 322 (2025), PII `S0360544225012824`: resolve the DOI
  and score the maritime Stackelberg model.
- Manzolli et al., “When Agents Meet,”
  [arXiv:2606.26400](https://arxiv.org/abs/2606.26400): verify the final
  version and model scope.
- Yao et al., [arXiv:2505.04532v1](https://arxiv.org/abs/2505.04532v1),
  7 May 2025: treat as a coordination lead because of the shared coauthor;
  any “nearest neighbor” label still requires canonical dimensional scoring.
- Supply-side pricing candidates
  [arXiv:2602.15722](https://arxiv.org/abs/2602.15722) and
  [arXiv:2603.25490](https://arxiv.org/abs/2603.25490): verify whether either
  changes the demand-side convex-hull-pricing/uplift scope.

### Exact-optimization and market-method leads

- Haslinger, Gaar, and Parragh,
  [arXiv:2504.13063](https://arxiv.org/abs/2504.13063).
- Wu, Li, and Lin, *Computers & Industrial Engineering* 206 (2025);
  DOI and version still to resolve.
- Zhou et al., *Transportation Research Part E* 196:103994 (2025);
  DOI and version still to resolve.
- Jacquillat and Lo,
  [arXiv:2407.02640](https://arxiv.org/abs/2407.02640).
- van Rossum, [arXiv:2606.10081](https://arxiv.org/abs/2606.10081).
- Gerbaux, Desaulniers, and Cappart,
  [DOI 10.1016/j.cor.2024.106848](https://doi.org/10.1016/j.cor.2024.106848);
  claim-level notes are pinned below.
- Gutierrez and Silvente,
  [arXiv:2601.20226](https://arxiv.org/abs/2601.20226), and Dumitrescu,
  Silvente, and Tankov,
  [arXiv:2410.12495](https://arxiv.org/abs/2410.12495): inspect their
  price-impact models without treating them as validation of this project's
  proposed affine approximation.
- Hyder et al.'s 2024 convex-hull-pricing survey and the article identified
  by PII `S0305054824002958`: resolve stable identifiers and full text.

### Empirical-motivation and ML-for-CO leads

- Yu et al., *Nature Communications* 16:8451 (2025), and the article
  identified by PII `S2352467725003595`: verify the reported sample sizes,
  peak effects, model assumptions, and stable DOIs before use.
- Bertsimas and Stellato (parametric mixed-integer strategy prediction);
  Xavier, Qiu, and Ahmed (SCUC reoptimization); Morabit, Desaulniers, and
  Lodi (column selection); Václavík et al.
  ([DOI 10.1016/j.ejor.2018.05.046](https://doi.org/10.1016/j.ejor.2018.05.046));
  [arXiv:2206.02568](https://arxiv.org/abs/2206.02568);
  [arXiv:2112.04906](https://arxiv.org/abs/2112.04906);
  [arXiv:2409.19678](https://arxiv.org/abs/2409.19678);
  [arXiv:2505.16952](https://arxiv.org/abs/2505.16952); and
  [arXiv:2311.14834](https://arxiv.org/abs/2311.14834) remain candidates for
  a scoped method review.

## Claim-level full-paper notes

All full-paper-derived claims retained in this inbox are in this section.
Each source is pinned to a stable record, a checked version/date, an access
date, and page-level locators. Statements labeled **transfer hypothesis** are
project proposals, not conclusions of the cited paper.

### Sugishita, Grothey, and McKinnon

Source: “Use of Machine Learning Models to Warmstart Column Generation for
Unit Commitment,” *INFORMS Journal on Computing* 36(4):1129–1146 (2024),
[DOI 10.1287/ijoc.2022.0140](https://doi.org/10.1287/ijoc.2022.0140);
[arXiv:2110.06872v2](https://arxiv.org/abs/2110.06872v2), version dated
15 December 2023. Accessed 2026-08-21.

- The repeated problems keep their structure and generator characteristics
  while demand forecasts change; the parameter is a demand vector in the
  coupling-constraint right-hand side (arXiv v2, pp. 1–4, §2, Eq. (2.1);
  p. 10, §4.1). For this project, that is a **close methodological analogue**,
  not an identity: a changing price vector may enter objective coefficients
  rather than the right-hand side.
- The tested neural model has four 1,000-unit tanh hidden layers with skip
  connections, while the k-nearest-neighbor comparator uses \(k=4\) solved
  instances (pp. 12 and 22, §4.2.2 and Appendix C, Figure 3).
- At a 0.25% prescribed gap, Table 4 reports LPR/double-sampling-network
  times of 60.8/36.6, 93.5/44.5, and 131.2/65.9 seconds for 200, 600, and
  1,000 generators, respectively: 1.66–2.10x for that named comparison, not
  a universal speedup (pp. 14–15, §4.3.3, Table 4). The stopping certificate
  uses a feasible primal value and a valid dual lower bound (pp. 5–6,
  Eqs. (2.6)–(2.7)).

**Transfer hypothesis:** test price-vector-conditioned dual warm starts
against both an unstabilized solve and reuse of the previous price-loop
iterate's duals.

### Kraul, Seizinger, and Brunner

Source: “Machine Learning–Supported Prediction of Dual Variables for the
Cutting Stock Problem with an Application in Stabilized Column Generation,”
*INFORMS Journal on Computing* 35(3):692–709 (2023),
[DOI 10.1287/ijoc.2023.1277](https://doi.org/10.1287/ijoc.2023.1277),
version of record published online 29 March 2023. Accessed 2026-08-21.

- The learned duals serve as centers in the du Merle penalized box
  formulation; the learned-center variant is contrasted with a classical
  variant that updates centers after every iteration (§3.1, p. 697,
  Eq. (5); §4.3.1, p. 706).
- When pricing finds no negative-reduced-cost column, the implementation
  halves the two penalty weights (§4.3.1, p. 706). Repeated halving does not
  itself reach zero in finitely many iterations. The paper's exact-recovery
  condition requires penalties to become zero after finitely many iterations
  and the center update condition to hold (§3.1, p. 697); this inbox therefore
  does not claim that the reported schedule alone proves exact LP recovery.
- SPARSE predicts one dual from five item-level inputs with two hidden
  layers of seven neurons; its dimensions do not depend on item count
  (§§3.2.5–3.2.6, pp. 699–700, Figure 3). It transfers across the tested
  controlled sizes but fails on some differently distributed BPPLIB classes
  (pp. 705–707, Tables 5–9). FULL has a fixed maximum input dimension and
  cannot process sizes above that maximum (pp. 699–700).
- The study generated 100,000 instances total, split into 80,000 for
  training/validation and 20,000 for testing—not 100,000 training instances
  (pp. 700 and 704, §4.2.1). Selected comparisons are near 2x, but results
  vary: for example, Table 7 reports 7.77 versus 3.76 seconds and 13.64
  versus 7.18 seconds in two named size/method comparisons (p. 706, Table 7).

**Transfer hypothesis:** if predicted box centers are tested here, specify
an explicit finite switch to an unstabilized, exact-pricing path rather than
inferring certification from geometric penalty decay.

### Shen et al.

Source: “Adaptive Stabilization Based on Machine Learning for Column
Generation,” *Proceedings of the 41st ICML*, PMLR 235:44741–44758 (2024),
[PMLR record and paper](https://proceedings.mlr.press/v235/shen24e.html);
[arXiv:2405.11198v1](https://arxiv.org/abs/2405.11198v1), version dated
18 May 2024. Accessed 2026-08-21.

- The adaptive rule is
  \(\epsilon=c_\epsilon^*/(c_\epsilon^*-1)\) when
  \(c_\epsilon^*<0\), and zero otherwise (PDF p. 5/PMLR p. 44745, §3.2,
  Eq. (15)). Lemma 3.5 proves finite arrival at zero for the paper's finite
  graph and exact-pricing setting (PDF p. 6/PMLR p. 44746; proof in
  Appendix C, PDF p. 13/PMLR p. 44753).
- Where multiple optimal dual solutions are available, training labels
  average their values (PDF p. 4/PMLR p. 44744, §3.1; Appendix E.2 and
  Table 7, PDF pp. 14–15/PMLR pp. 44754–44755). This is an empirical
  treatment of label ambiguity, not proof that degeneracy is eliminated.
- On the out-of-distribution GCB benchmark, the FFNN has lower displayed
  error and fewer ASCG iterations than the GCN (PDF p. 8/PMLR p. 44748,
  Table 4); this is benchmark-specific.
- In the exact-pricing GCB comparison, iterations fall from 155.1 to 86.6
  (44.2%) while time falls from 17.8 to 16.1 seconds (9.6%). The paper
  attributes part of the difference to denser stabilized duals making
  pricing harder (PDF pp. 7–8/PMLR pp. 44747–44748, Tables 1–2 and §4.3).

### You et al.

Source: “Learned Pairwise Deep Dual-Optimal Inequalities for Stabilizing
Column Generation,”
[DOI 10.48550/arXiv.2607.13373](https://doi.org/10.48550/arXiv.2607.13373);
[arXiv:2607.13373v1](https://arxiv.org/abs/2607.13373v1), version dated
15 July 2026. Accessed 2026-08-21. The checked manuscript is an arXiv
preprint submitted to, not a published article in, *INFORMS Journal on
Computing*.

- CAPSC samples \(K=20\) points from the optimal dual face and jointly
  retains at least \(\lceil0.8K\rceil\) samples. Every selected pair must
  satisfy the margin on every retained sample; this is not simply an
  independent “true in 80% of samples” vote (§4.2, pp. 9–10,
  Eqs. (3)–(4); §5.1.4, p. 17).
- XGBoost uses customer-, pair-, and instance-level feature groups
  (§4.3, pp. 11–12; EC Table EC.1, PDF pp. 26–27). Retained relations
  enter as zero-cost artificial columns (§4.5, p. 13).
- Algorithm 1 releases active artificial variables and ends with exact
  pricing. Under exact LP solutions, exact activity detection, exact final
  pricing, and no early gap stop, the paper proves finite recovery of the
  baseline bound (§4.5, pp. 13–14, Proposition 3 and Algorithm 1;
  Corollary EC.1, PDF p. 35).
- Tables 2 and 6 report 54.8% and 83.1% root-CG time reductions with a
  displayed 0.0% bound difference for CVRP and VRPTW, respectively
  (pp. 18 and 21). Those figures exclude prediction/postprocessing overhead
  and are not whole-solver speedups.
- The \(2m\) auxiliary optimization problems discussed on p. 10 are the
  exhaustive full-face test that CAPSC avoids; they are not CAPSC's label
  cost.

### Gerbaux, Desaulniers, and Cappart

Sources:

- Gerbaux, Desaulniers, and Cappart, “A machine-learning-based column
  generation heuristic for electric bus scheduling,” *Computers &
  Operations Research* 173:106848 (January 2025),
  [DOI 10.1016/j.cor.2024.106848](https://doi.org/10.1016/j.cor.2024.106848),
  version of record available online 25 September 2024; and
- Juliette Gerbaux, *Résolution heuristique par génération de colonnes et
  apprentissage automatique du problème d'horaires d'autobus électriques*,
  master's thesis, Polytechnique Montréal, May 2023,
  [stable repository record](https://publications.polymtl.ca/53409/).

Both accessed 2026-08-21.

- The hybrid reduced network unions greedy-solution arcs with arcs whose
  predicted incoming or outgoing rank is at most two, while always retaining
  designated nonselectable arcs (article §5.2.4–§5.3, p. 7, Algorithm 2;
  thesis §§4.2.2–4.2.3, printed pp. 32–33/PDF pp. 49–50).
- The hybrid's 1.4% average cost gap is lower than the GNN-only 12.4% in the
  reported comparison, but this is empirical evidence, not proof that the
  union guarantees quality (article p. 10, Table 4; thesis printed
  pp. 45–46/PDF pp. 62–63, Table 5.6).
- The published method is heuristic: it fixes a reduced pricing network and
  has no full-network exact fallback (article §§4.3 and 5, p. 5).
- The thesis's cross-network test reports 35.06% and 48.44% gaps (printed
  p. 49/PDF p. 66, Table 5.9). The 1055.63% result is instead a same-network
  size/distribution transfer for the GNN-only method (printed p. 48/PDF
  p. 65, Tables 5.1 and 5.8), so it is not evidence for a “wrong-road-network
  model” claim.
- Instance counts vary by type, and the 465.5–19,300.3-second figures are
  upstream branch-and-price solve times used to create labels, not measured
  label-extraction times (thesis printed pp. 37 and 40/PDF pp. 54 and 57,
  Tables 5.1 and 5.3; article p. 8, Table 2).

**Transfer hypothesis:** a pricing-network reduction would need a
full-network exact-pricing fallback before it could participate in this
project's certification path.

### Wang and Khir

Source: “Learning to Control Stabilization in Column Generation,”
[DOI 10.48550/arXiv.2604.23889](https://doi.org/10.48550/arXiv.2604.23889);
[arXiv:2604.23889v2](https://arxiv.org/abs/2604.23889v2), version dated
6 May 2026. Accessed 2026-08-21.

- On the highly degenerate Gen_4 benchmark, smoothing reduces iterations by
  4–8% while increasing runtime by 12–18%, and penalization worsens both
  iteration and runtime results; other benchmark reversals also occur
  (§5.2, p. 12, Table 1).
- The paper describes policy inference overhead as negligible, but later
  names RL inference overhead together with harder stabilized pricing as
  possible contributors to Gen_4 runtime. It does not isolate inference
  time, so this inbox does not attribute the reversal to inference alone
  (§§5.1–5.2, pp. 11–12).
- Its convergence claims are conditional on exact pricing, finite columns,
  and fallback/switching safeguards. Lemma 2 gives finite convergence under
  an eventual separating fallback, and Proposition 3 covers smoothing when
  the predicted reference is used only finitely before a standard rule
  (§§3.2.2–3.3, pp. 7–8; proof on p. 23). These are safeguard guarantees,
  not a convergence-rate guarantee for the learned policy alone.

## Local experiment hypotheses, not literature conclusions

If these candidates survive cite-and-scope review, an experiment brief could
compare:

1. previous-iterate dual reuse, k-nearest-neighbor warm starts, and a learned
   dual predictor;
2. learned pricing-network reduction with mandatory full exact pricing as a
   fallback;
3. strategy/support prediction; and
4. pricing-call triage.

The brief would need to preregister solver and gap settings, label
canonicalization, instance-level splits, the price-perturbation distribution,
out-of-range handling, fallback triggers, and separate iteration and
wall-clock measures. These are proposed controls, not a design contract
validated by the papers above.

## OMIE market-curve lead: corrected status

### Source register

All sources in this subsection were accessed 2026-08-21.

- OMIE,
  [aggregate curve file listing](https://www.omie.es/en/file-access-list?parents=/Day-ahead%20Market/3.%20Curves&dir=Aggregate%20supply%20and%20demand%20curves%20of%20Day-ahead%20market&realdir=curva_pbc)
  and [download FAQ](https://www.omie.es/en/faq/system-access), undated live
  pages.
- OMIE, *Modelo de Ficheros para el Intercambio de Información entre OM y
  Agentes*, version 1.37, 30 September 2025,
  [official PDF](https://www.omie.es/sites/default/files/2025-09/formato_ficheros_inf_pub_137_1.pdf):
  revision history p. 3; common format §3, p. 6; `marginalpdbc` §5.1.1.1,
  p. 13; daily curve format §5.1.3.1, pp. 24–26.
- OMIE, [Legal Warning](https://www.omie.es/en/legal-warning), undated live
  terms.
- OMIE, *Go-live of the 15-minute Market Time Unit in the Day-Ahead Market*,
  1 October 2025,
  [official notice](https://www.omie.es/sites/default/files/2025-10/2501001_go_live_mtu15_md_en_vf.pdf),
  p. 1.
- CNMC, consolidated day-ahead and intraday market rules, Resolution of
  30 July 2026, BOE 11 August 2026,
  [official PDF](https://www.boe.es/boe/dias/2026/08/11/pdfs/BOE-A-2026-17570.pdf):
  Rule 30.3, PDF pp. 67–68; Annex 1, PDF pp. 175–179.
- NEMO Committee, *EUPHEMIA Public Description*, 18 December 2025,
  [official PDF](https://nemo-committee.eu/assets/files/euphemia-public-description.pdf):
  simple/complex orders §§5.1, 5.3–5.4, pp. 25–38; welfare and network
  constraints §6, pp. 41–42; block decisions §§7.4–7.5, pp. 48–52;
  reinsertion §§7.7–7.8, p. 58; precision §8.1, p. 69.

### Access and format observations

- Public daily downloads currently work without authentication using
  `https://www.omie.es/en/file-download?parents=curva_pbc&filename=curva_pbc_YYYYMMDD.1`.
  This is a live download convention, not a guaranteed API or retention
  contract.
- Post-MTU15 files are not approximately 4 MB/day. Observed downloads were
  17,838,683 bytes for delivery date 2025-10-01 and 21,643,146 bytes for
  2026-08-20; the normal observed post-MTU15 range was roughly 16–22 MiB.
  The 2026-08-21 publication was 15,651,818 bytes and schema-incomplete
  relative to version 1.37, which is itself a regression case rather than
  evidence of a stable size/schema guarantee.
- Version 1.37 documents semicolon-delimited text and locale-formatted
  numbers (§3, p. 6). Latin-1 encoding and CRLF were observed in sampled
  files but are not guaranteed by that document. A parser should identify
  the named field row rather than blindly skip two physical lines.
- In `Tipo Oferta`, `C` means buy/demand and `V` means sell/supply; in the
  separate offered/matched column, `O` means offered and `C` means matched
  (version 1.37, §5.1.3.1, pp. 24–25). The overloaded `C` must be interpreted
  with its column name.
- MTU15 clearing began on 30 September 2025 for delivery on 1 October 2025
  (OMIE go-live notice, p. 1). The market calendar has 96 periods on a normal
  day, 92 on the spring DST transition, and 100 on the autumn transition—not
  23/25 periods (2026 market rules, Annex 1, PDF pp. 175–176).

### What the curves do not validate

A naive supply/demand step-curve intersection must **not** be claimed to
reproduce `marginalpdbc`. Period aggregation omits cross-period and
cross-zone constraints needed to reconstruct block, scalable complex,
exclusive, import/export, and market-coupling decisions. EUPHEMIA maximizes
welfare over coupled periods and zones, includes integer decisions and
network constraints, and permits paradoxically rejected orders (2026 market
rules, Rule 30.3, PDF pp. 67–68; EUPHEMIA §§5.3–6 and 7.4–7.8, pp. 31–58).
The published matched series is already a clearing output, and its displayed
prices are transformed/rounded values rather than a lossless serialization of
the clearing model (OMIE format v1.37, pp. 24–26; EUPHEMIA §8.1, p. 69).
An occasional numerical match would therefore be a coincidence, not a valid
regression oracle.

### Calibration and reuse gate

OMIE calibration remains exploratory. Do not call it validated until this
repository contains both:

1. a committed, schema-aware parser; and
2. a dated, immutable regression fixture with source filenames, access
   dates, checksums, expected parsed outputs, and cases covering a normal
   MTU15 day, both DST transitions, market splitting/complex typologies,
   locale parsing, and a malformed or schema-incomplete publication.

Any fitted slope must be described as a **researcher-derived descriptive
estimate** from a specified curve representation and local window. It is not
an OMIE-published value, a causal response, or the derivative of the full
EUPHEMIA clearing map. Publication or redistribution remains subject to
OMIE's applicable attribution and reuse terms. Cite OMIE, identify delivery
and access dates and filenames, preserve checksums, and disclose
transformations. OMIE's Legal Warning is not an explicit standard open-data
license, so this inbox does not assert that fitted slopes are freely
publishable.

Nord Pool, EPEX, ENTSO-E, ERCOT, PJM, CAISO, and MISO remain unverified
alternative data leads. Product coverage, prices, retention, access, and
reuse terms require primary-source checks in the separate cite-and-scope
work; no negative availability claim is established here.

## Cite-and-scope handoff

Before a candidate can change any canonical file, the follow-up PR should:

1. deduplicate by normalized DOI/arXiv identifier;
2. pin the stable identifier, version/date, and access date;
3. verify claim-level page/table locators from full text;
4. score Duties, EndogP, Exact, evidence tier, and relevance under the
   canonical rubric; and
5. record both supporting and collision evidence in the four canonical
   literature files together.
