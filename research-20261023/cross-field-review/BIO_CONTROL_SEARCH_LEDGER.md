# Biology/control/robotics search ledger

Date: 2026-10-23. Research-only work in `/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017`. No citation-count ranking, exhaustive Scholar screening, execution or reproduction claimed. Google Scholar was attempted directly, then the ordinary web search index was used to find primary papers. The resulting review is a targeted cross-disciplinary scan, not a systematic review or an assertion of novelty.

## Direct Google Scholar attempts

Project-level Google Scholar search subsequently succeeded through the parent agent’s browser session; see the parent search ledger. The following limitation applies only to this agent’s backend attempts.

Both direct opens returned tool “Internal Error” with “URL ... is not accessible via this tool.” No result page was readable, no counts or rankings collected, and no CAPTCHA bypass attempted.

1. Exact query: `metabolic gap filling MILP OptKnock shadow prices`
   URL: https://scholar.google.com/scholar?q=metabolic+gap+filling+MILP+OptKnock+shadow+prices
2. Exact query: `predictive safety filter learning model predictive control recursive feasibility`
   URL: https://scholar.google.com/scholar?q=predictive+safety+filter+learning+model+predictive+control+recursive+feasibility

## Fallback web searches, exact query strings

Executed through `web.run.search_query`, without domain restrictions. Only primary article/manuscript, author repository and primary bibliographic records support the review; incidental aggregators and Wikipedia were not used as evidence.

Batch 1:
- `OptKnock bilevel programming framework identifying gene knockout strategies 2003 Burgard Pharkya Maranas`
- `FastGapFill efficient gap filling metabolic networks 2014 Thiele Vlassis Fleming`
- `predictive safety filter learning based control Wabersich Zeilinger 2021`
- `Learning model predictive control recursive feasibility Rosolia Borrelli 2017 safe set`

Batch 2:
- `Reed Patel Chen Joyce Applebee Herring Bui Knight Fong Palsson 2006 systems approach refining genome annotation gap filling SMILEY`
- `Mahadevan Schilling 2003 effects alternate optimal solutions flux balance analysis flux variability`
- `COBRApy Ebrahim Lerman Palsson Hyduke 2013 constraints based reconstruction analysis python`
- `PDDLStream Garrett Lozano Perez Kaelbling 2020 optimistic adaptive planning sampling`

Batch 3:
- `Varma Palsson 1994 metabolic flux balancing basic concepts scientific practical use shadow prices`
- `Mayne Rawlings Rao Scokaert 2000 constrained model predictive control stability optimality Automatica`
- `Wang Garrett Kaelbling Lozano Perez active model learning diverse action sampling task motion planning 2018`

Discovery from results also surfaced `Active Learning of Abstract Plan Feasibility` (Noseworthy et al.), subsequently opened directly. No separate search query was executed for that title.

## Primary source access and selection

| Target | What was accessed | Selection / limitation |
|---|---|---|
| OptKnock, Burgard et al. 2003 | Publisher record https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/abs/10.1002/bit.10803 (search extraction); author group https://www.maranasgroup.com/submission/optknock_2.htm (search extraction); full 11-page PDF https://cepac.cheme.cmu.edu/pasilectures/costas/burgard-etal03a.pdf (direct open, 805 extracted lines). | Included. Final volume/pages from publisher; manuscript first page contains placeholder volume/pages and must not override publisher metadata. Bilevel LP response is structurally informative, not transferable unchanged to integral routing. |
| SMILEY / Reed et al. 2006 | Primary indexed article extraction https://pmc.ncbi.nlm.nih.gov/articles/PMC1859954/; PubMed https://pubmed.ncbi.nlm.nih.gov/17088549/ search record includes title/authors/DOI/pages. Direct PMC open returned a browser/reCAPTCHA check, not full text. | Included with restricted depth. No detailed theorem claim rests on inaccessible text. |
| fastGapFill, Thiele et al. 2014 | Publisher record https://academic.oup.com/bioinformatics/article/30/17/2529/2748200?searchresult=1; full three-page PDF https://academic.oup.com/bioinformatics/article-pdf/30/17/2529/48927713/bioinformatics_30_17_2529.pdf opened, 193 lines. PMC https://pmc.ncbi.nlm.nih.gov/articles/PMC4147887/ search extraction readable but direct open returned browser check. | Included. Distinguish this paper from the separate 2014 paper titled “Efficiently gap-filling reaction networks.” |
| Mahadevan & Schilling 2003 | PubMed primary abstract/bibliography https://pubmed.ncbi.nlm.nih.gov/14642354/, DOI 10.1016/j.ymben.2003.09.002. | Included abstract-level. Two-optimization variability concept and alternate-solution motivation only; no detailed reproduction of original algorithm. |
| COBRApy 2013 | DOI direct open https://doi.org/10.1186/1752-0509-7-74 failed; canonical publisher https://link.springer.com/article/10.1186/1752-0509-7-74 opened full text, 382 lines. | Included as concrete open tool. Package not installed, current API not checked, not an EGG solver replacement. |
| Predictive safety filter 2021 | Publisher https://www.sciencedirect.com/science/article/pii/S0005109821001175 search extraction; https://arxiv.org/abs/1812.05506; full https://arxiv.org/html/1812.05506 opened, 588 lines; second targeted open at line 125 exposes Algorithm 1 fallback. | Included. Manuscript v4 dated 17 May 2021. Probabilistic model and safe terminal requirements limit theorem transfer. |
| LMPC, Rosolia & Borrelli | https://arxiv.org/abs/1609.01387 search record; full https://arxiv.org/html/1609.01387 opened, 762 lines; targeted open at line 179 exposes sampled cost definition. | Included, author manuscript v7 dated 14 Dec 2017. Repeated initial condition, constraints and objective explicitly read in introduction. Avoid asserting generalization guarantee across new EGG families. |
| Linear convex LMPC extension | https://arxiv.org/abs/1702.07064 search record/abstract. | Not counted separately; useful warning that convex safe-set acceleration requires linear/convex structure. |
| PDDLStream 2020 | https://ojs.aaai.org/index.php/ICAPS/article/view/6739 opened, 66 lines; title/authors/DOI/venue/pages verified. https://github.com/caelan/pddlstream appears in search results. | Included at proceedings abstract depth; no proof/completeness theorem independently checked, no software execution. |
| Active model learning / Wang et al. 2018 | https://arxiv.org/html/1803.00967 opened full text, 347 lines; author PDF https://lis.csail.mit.edu/pubs/wang-iros18.pdf and institutional PDF https://cbmm.mit.edu/sites/default/files/documents/wang-iros18%20%281%29.pdf appeared in search extraction. | Included. Manuscript v2 verifies IROS 2018; page range/DOI not asserted. |
| Abstract plan feasibility / Noseworthy et al. 2021 | https://arxiv.org/html/2107.00683 opened full text, 350 lines; version v1 dated 1 July 2021, authors visible. | Included explicitly as arXiv preprint; later journal/conference publication not verified. |
| Varma & Palsson 1994 | Primary publisher https://www.nature.com/articles/nbt1094-994 and author-affiliated record https://iris.hi.is/en/publications/metabolic-flux-balancing-basic-concepts-scientific-and-practical-/ via search extraction. | Background only, not counted among ten. Did not establish a new EGG price-support result. |
| Mayne et al. 2000 | Publisher https://www.sciencedirect.com/science/article/pii/S0005109899002149 and author-affiliated https://experts.illinois.edu/en/publications/constrained-model-predictive-control-stability-and-optimality/ through search extraction; mirror PDF discovered. | Excluded from ten-primary-source count because this is a survey. Classical MPC context only; concrete fallback drawn from primary predictive-filter/LMPC papers. |

## Interpretation checks and negative results

- No biology source found here establishes market-clearing linear-price support for integral, power-coupled vehicle routing.
- No safe-control theorem read here establishes deadline performance of EGG's mixed-integer completion routine.
- Flux consistency is weaker than one simultaneous physically complete fleet schedule; direct use as a feasibility certificate rejected.
- Convex safe-set interpolation can mix incompatible discrete route choices; direct transplantation rejected.
- Incumbent non-use cannot establish a negative edge label. Feasible/infeasible/timeout statuses must be separate.
- The two ranked EGG tests and engineering durations in the companion review are planning proposals, not measured results.
