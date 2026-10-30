# EV/OR search and access ledger

Date: 23 October 2026. Researcher: delegated EV/OR literature agent. Only EV_OR_REVIEW.md and this ledger authored. No experiments, training, private data, or solver execution.

## Direct Google Scholar attempts

| Exact query | URL / outcome |
|---|---|
| electric bus scheduling column generation charging 2024 | https://scholar.google.com/scholar?q=electric+bus+scheduling+column+generation+charging+2024 — web backend reported inaccessible URL |
| machine learning arc selection column generation crew scheduling | https://scholar.google.com/scholar?q=machine+learning+arc+selection+column+generation+crew+scheduling — web backend reported inaccessible URL |

These are backend access failures, not evidence Scholar is globally unavailable. Parent researcher accessed Google Scholar through the in-app browser with query `machine learning column generation electric bus scheduling` and supplied Olson/Lusby/Røpke 2026 and Montanaro et al. 2025 leads. This agent verified both against institutional/publisher primary records. Parent owns the browser observations; this ledger does not claim direct observation of those results.

## Exact fallback web queries

1. `electric vehicle scheduling column generation charging Diefenbach 2023 2024`
2. `Gerbaux Desaulniers Cappart 2025 graph reduction vehicle scheduling`
3. `machine learning column generation crew scheduling Morabit Desaulniers Lodi 2021`
4. `learning to solve large scale security constrained unit commitment Xavier Qiu Ahmed 2021`
5. `Subpath-Based Column Generation Electric Routing Scheduling Problem 2407.02640 authors`
6. `electric bus scheduling time of use electricity prices column generation 2024 2025`
7. `machine learning column selection column generation Morabit 2021 doi`
8. `Solving Mixed Integer Programs Using Neural Networks Nair 2020 neural diving arxiv`
9. `On the role time of use electricity price charge scheduling Zhang authors 13134`
10. `Electric Vehicle Fleets Scalable Route Recharge Scheduling column generation authors 2104.03823`

Search results were used for discovery; technical claims in report are attached to primary paper, author repository, publisher, or university records. No citation counts are relied upon.

## Follow-through / evidence depth

| Source | Primary access achieved | Limitation / version issue |
|---|---|---|
| Gerbaux, Desaulniers, Cappart 2025 | UCLouvain record and 14-page published PDF; inspected greedy selection, protected arcs, labels, hybrid union and experiment discussion | Selective reading, no replication |
| de Vos, van Lieshout, Dollevoet 2024 | TU Eindhoven institutional abstract and metadata | 2022 arXiv abstract contains older computational results; report uses published 2024 abstract, not old results |
| Zhang, Wang, Gu, Han, Chung, Qu 2024 | PolyU 20-page PDF; inspected assumptions and single-terminal round-trip formulation | PDF accepted 2023 and citation footer says 2023; published issue is 2024; distinguish online/issue year |
| Lu, Xing, Li 2025 | Publisher-indexed title, authors, issue, abstract and highlights | Direct ScienceDirect page returned 403. No full-text algorithm claims |
| Parmentier, Martinelli, Vidal | arXiv author record and 41-page PDF, v2 February 2023 | Preprint first submitted 2021; no final journal year inferred |
| Jacquillat, Lo | arXiv current record and authors' ElectricRouting.jl README | Initial 2024 title differs from September 2026 v3; original HTML timed out. Current and original abstract claims explicitly distinguished |
| Morabit, Desaulniers, Lodi arc selection | arXiv 2022 record and 32-page PDF; inspected exact-pricing discussion and applications | Cite preprint year; final publication metadata not inferred |
| Morabit, Desaulniers, Lodi column selection 2021 | INFORMS publisher abstract, DOI and metadata | Abstract-level only |
| Xavier, Qiu, Ahmed | arXiv 36-page PDF selectively inspected; journal DOI/year cross-check | 2019 preprint vs 2021 journal stated distinctly |
| Nair et al. | arXiv record and complete 19-author list | Abstract-level only; short citation points to full list |
| Olson, Lusby, Røpke 2026 | DTU full conference abstract reproduced on record | Two-page ROUTE conference abstract; preliminary results, no journal-level proof/replication claim |
| Montanaro, Jacquet, Cappart, Desaulniers 2025 | Springer and UCLouvain abstracts, authors, DOI, LNCS pages | Institutional PDF is entire 19.91 MB proceedings; backend rejected >10 MiB. No full-text pruning-rule claim |

## Additional discovered sources not promoted to core twelve

- Diefenbach, Emde, Glock (2023), multi-depot intralogistics EVSP with nonlinear charging, DOI https://doi.org/10.1016/j.ejor.2022.06.050. Useful branch-and-check alternative; less direct to shared tariff/supply mechanism.
- Wu, Lin, Liu, Jin (2022), *The multi-depot electric vehicle scheduling problem with power grid characteristics*, TR-B 155, 322–347. Found in Montanaro publisher reference list; **not independently retrieved**, so no mechanism or novelty conclusions based on title alone. High-priority next read for supply coupling.
- `Adaptive Partitioning in Column Generation for Nested Paths`, arXiv:2605.28692 surfaced in fallback search. Not followed; no claims made about authors, results or fit.

## Key cautions for synthesis

The 2026 Olson abstract directly describes reduced graphs, stagnation-triggered progressive restoration, and eventual full graph. This substantially narrows any proposed recovery novelty claim. Montanaro 2025 makes GRASP/pruning an essential nonlearned comparison. Neither abstract establishes that EGG's precise supply-and-tariff coupling is already solved; a detailed formulation comparison remains necessary. The review's proposed experiments and bound-direction explanation are this agent's analysis, not attributed empirical findings.

## Follow-up primary checks

Wu et al. 2022 institutional accepted manuscript retrieved and formulation selectively inspected; see GRID_EV_OVERLAP_NOTE.md, which supersedes the earlier not-retrieved status. Exact query: `"The multi-depot electric vehicle scheduling problem with power grid characteristics"`. Parmentier final 2023 Transportation Science metadata verified at IP Paris institutional record, DOI 10.1287/trsc.2023.1199; prior preprint-only metadata status is superseded. Exact query: `"Electric Vehicle Fleets" "Parmentier" "Martinelli" "Vidal" Transportation Science`.
