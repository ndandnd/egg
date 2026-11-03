# Cross-field search ledger — parent integration

Research date and cutoff: **23 October 2026**. User requested a broad Google Scholar search spanning EVSP, electricity, ML and analogous problems in other disciplines. This is a structured exploratory review, not an exhaustive systematic review or a novelty clearance. Search ranking, citation counts and paper-reported speedups are not treated as EGG evidence.

## Google Scholar access and exact queries

Direct Scholar URLs failed through the web-search backend for the parent and delegated agents. **The parent successfully read actual Scholar results in the in-app browser**, without a CAPTCHA or authentication change. The following seven queries returned visible results. The first result page was inspected for each; we did not screen every hit or every page.

| Exact query | Selected leads followed or triaged |
|---|---|
| `machine learning column generation electric bus scheduling` | Gerbaux et al.2025; Olson/Lusby/Røpke2026 conference abstract; Montanaro et al.2025 nonlearned GRASP comparator; Morabit et al.; Parmentier et al. |
| `selected configuration interaction machine learning` | Coe2018; Nie et al.2026 ranking loss; Casier et al.2026; Pineda Flores2021 Chembot; additional active-learning/RL configuration-interaction leads. |
| `metabolic network gap filling flux variability optimization` | fastGapFill; optimization-based curation; Meneco; gapseq; EnsembleFBA. The final core set follows primary references to variability analysis and OptKnock rather than assuming every search hit was read. |
| `learning augmented optimization safe screening` | Noisy cross-field query; identified Christianson et al.2024 ICNN contingency screening. Generic biomedical/LLM hits excluded. A 2026 CASP preprint was not promoted to a checked core source. |
| `"electric bus" "time of use" column generation` | Confirmed Zhang et al. TOU scheduling; additional mixed-fleet, robustness and grid-stability leads were not promoted without primary checks. |
| `"predictive safety filter" learning optimization` | Predictive safety filtering, barrier functions, system-level synthesis and conformal variants. Core claims use the primary papers inspected in BIO_CONTROL_REVIEW.md, not Scholar snippets. |
| `"safe screening" duality gap` | Gap Safe2015/2017; Dantas2021; Massias2017 working sets. Recent unrelated variants were not pursued merely because they were newer. |

Scholar entries were discovery signals. Technical statements below are sourced to publisher proceedings, author manuscripts, institutional records or official author software repositories. The three delegated ledgers record their own backend failures and exact additional web queries. Those failures do not contradict the successful browser search.

## Search organization and follow-through

Three GPT-6.1 Sol workers handled (a) electric-bus scheduling/decomposition, (b) chemistry/quantum algorithms, and (c) biological networks/control/robotics. The parent checked screening, verification, learning-augmented algorithms and continuous warm starts. A separate bounded integration pass challenged the proposed transfers; it is an internal review, not external peer review.

- **EV/OR:** [review](EV_OR_REVIEW.md), [queries/access ledger](EV_OR_SEARCH_LEDGER.md). Twelve core entries; direct bus overlap, nonlearned sparsification, pricing and master-pool selection, repeated unit-commitment MIPs and neural diving.
- **Chemistry/quantum:** [review](CHEM_QUANTUM_REVIEW.md), [ledger](CHEM_QUANTUM_SEARCH_LEDGER.md). Ten core entries; selected CI, adaptive VQE, active spaces and reaction-network exploration. Nie et al. publication on20August2026 was verified; no future publication is used. Dice and Quantum Package code/license observations are in the ledger; neither was installed or run.
- **Biology/control/robotics:** [review](BIO_CONTROL_REVIEW.md), [ledger](BIO_CONTROL_SEARCH_LEDGER.md). Ten core entries; gap filling, alternative solutions, predictive filters, stored trajectories, symbolic/continuous planning and active feasibility learning.
- **Math/verification:** [review](MATH_VERIFICATION_REVIEW.md). Seven entries, including two publications in the same Gap Safe lineage. Publisher abstracts/full texts accessed as stated for each row.
- **Power screening:** [additional note](POWER_SCREENING_NOTE.md). Primary full HTML and assumptions checked after a Scholar lead; conservative acceptance has a specific continuous-model scope.
- **Skeptical integration:** [challenge](INDEPENDENT_SYNTHESIS_CHALLENGE.md). Does not add an independent dataset or count as an additional publication.

Additional supply-coupling follow-through is complete in [GRID_EV_OVERLAP_NOTE.md](GRID_EV_OVERLAP_NOTE.md): Wu et al.2022's accepted manuscript was selectively inspected. The four main reviews contain39 source entries, and the power/grid follow-ups add2, for41 core entries. No tally of Scholar hits is asserted. Source entries are not all independent research lines; dates include explicitly identified preprints and conference abstracts.

## Parent primary-source access

| Source | Access achieved | Limit |
|---|---|---|
| Ndiaye et al.2015 | NeurIPS nine-page PDF, model and dual assumptions | Selected sections; no theorem implementation reproduced |
| Ndiaye et al.2017 | JMLR abstract, authors, volume/article/pages | Full extended proof not audited |
| Dantas et al.2021 | JMLR abstract and bibliography | Local-regularity proof not audited |
| Massias et al.2017 | arXivv2 abstract and version history | No full algorithm reproduction |
| Bamas et al.2020 | NeurIPS twelve-page PDF, introductory theorem/formulation | Online covering assumptions deliberately distinguished from EGG |
| Sambharya et al.2023 | PMLR record and fifteen-page PDF | Convex-QP model/architecture inspected; no generalization-proof reproduction |
| Clarke et al.2000 | Author-hosted sixteen-page PDF and author bibliography | Some extracted equations garbled; claims limited to readable framework/abstraction direction |

An attempted NeurIPS abstract URL for Grigorescu et al.2022 returned a cache miss; the paper is not a core basis for the synthesis. The parent does not claim every full-text link on every results page was accessible. Agent ledgers disclose inaccessible publisher pages, PMC checks and the oversized Montanaro proceedings PDF.

## Inclusion, limits and reproducibility

Core sources must share a concrete decision structure with EGG or define a crucial novelty baseline: learned restriction, costly joint completion, many alternative witnesses, coupled-resource sensitivity, candidate recovery, or valid certificates. Keyword overlap alone is insufficient. Reviews and search snippets can suggest sources but do not establish technical guarantees. Abstract-only papers support scope/priority warnings, not detailed implementations.

Only public literature and existing authorized compact EGG research receipts were used. No sealed data, cluster access, numerical solver, training, or new experiment was used in this review. Proposed engineering and CPU estimates are planning judgments; they are not measured runtime or prospective launch authorization. Store paper links and original analysis, not copies of full copyrighted papers in the Git backup.
