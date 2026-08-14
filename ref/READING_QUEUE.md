# Reading queue

Last updated: 2026-08-14 (closure pass: consolidated into one ranked table).

One global priority queue for full-text acquisition and audit. Keys refer to
`papers.csv`. "Gates" points to the brainstorm ideas (B1-B34, see
`BRAINSTORM_20260814.md`) or decisions a read blocks. Access: OA = open
access / preprint available; PW = paywalled (needs library); ? = check.
Statuses: `need-pdf` -> `have-pdf` -> `audited` (audited items get paper-level
notes in `review_notes/` and their matrix row re-scored). The 17 already
audited papers are not queued; their sources are in `papers/`.

Update rule: when a PDF is acquired or an audit completes, update the Status
column in the same commit as the notes.

## Ranked queue

| # | Key | Short citation | Identifier | Gates | Access | Status |
|---|---|---|---|---|---|---|
| 1 | yao2025 | Yao, Liu, Scaglione, Bekhor, Zhang 2025 | arXiv:2505.04532 | whole-thesis positioning; coordinate with Scaglione first | OA | need-pdf |
| 2 | najafi2023 | Najafi & Fripp 2023, Energy & AI | 10.1016/j.egyai.2023.100277 (arXiv:2302.00166) | B1, B2 differentiation | OA | need-pdf |
| 3 | dantzigwolfebilevel2025 | DW single-level MIBLP reformulation, Opt. Online 2025 | (preprint) | Chapter I / Direction A scope | OA | need-pdf |
| 4 | andrianesis2022 | Andrianesis, Bertsimas, Caramanis, Hogan | 10.1109/TPWRS.2021.3122000 (arXiv:2012.13331) | B3 | OA | need-pdf |
| 5 | anunrojwong | Anunrojwong, Balseiro, Besbes, Xu | SSRN 4877753 | B8 | OA | need-pdf |
| 6 | jiang2026 | Jiang, Nie, Skoulakis 2026 | arXiv:2602.19660 | B8 | OA | need-pdf |
| 7 | briant2008 | Briant et al. 2008, Math. Prog. | (see notes; INRIA PDF) | B1 | OA | need-pdf |
| 8 | dumerle1999 | du Merle, Villeneuve, Desrosiers, Hansen 1999 | 10.1016/s0012-365x(98)00213-1 | B2 | PW | need-pdf |
| 9 | frangioni2002 | Frangioni 2002, SIAM J. Opt. | 10.1137/s1052623498342186 | B2 | PW | need-pdf |
| 10 | pessoa2018 | Pessoa, Sadykov, Uchoa, Vanderbeck 2018 | 10.1287/ijoc.2017.0784 | B2 | PW | need-pdf |
| 11 | gribik2007 | Gribik, Hogan, Pope 2007 (working paper) | (lmpmarketdesign.com) | B3, B16 | OA | need-pdf |
| 12 | oneill2005 | O'Neill et al. 2005, EJOR | 10.1016/j.ejor.2003.12.011 | B3, B16, B17 | PW | need-pdf |
| 13 | baumol1964 | Baumol & Fabian 1964, Mgmt. Sci. | 10.1287/mnsc.11.1.1 | spine (internal prices fail) | PW | need-pdf |
| 14 | scarf1994 | Scarf 1994, JEP | 10.1257/jep.8.4.111 | spine (indivisibilities) | OA | need-pdf |
| 15 | ma2013 | Ma, Callaway, Hiskens 2013 | 10.1109/tcst.2011.2174059 | B1, B10 | PW | need-pdf |
| 16 | gan2013 | Gan, Topcu, Low 2013 | 10.1109/TPWRS.2012.2210288 | B1, B10 | PW | need-pdf |
| 17 | roozbehani2012 | Roozbehani, Dahleh, Mitter 2012 | 10.1109/tpwrs.2012.2195037 | B10, B11 | PW | need-pdf |
| 18 | kazempour2015 | Kazempour, Conejo, Ruiz 2015 | 10.1109/tpwrs.2014.2332540 | B9 | PW | need-pdf |
| 19 | bailey2025 | Bailey, Brown, Myers, Shaffer, Wolak 2025 | 10.1257/aeri.20240476 | B8 motivation | PW | need-pdf |
| 20 | kuehnbach2021 | Kuehnbach, Stute, Klingler 2021 | 10.1016/j.esr.2020.100608 | B8 motivation | ? | need-pdf |
| 21 | cornelusse2019 | Cornelusse et al. 2019, Applied Energy | 10.1016/j.apenergy.2019.03.109 | B15 | PW | need-pdf |
| 22 | yetkin2024 | Yetkin, Augustino, Lamadrid, Snyder 2024 | 10.1007/s11081-023-09878-w | dictator positioning; same journal as own submission | PW | need-pdf |
| 23 | karasavvidis2024 | Karasavvidis, Papadaskalopoulos, Strbac 2024 | 10.1109/TEMPR.2024.3414988 | B18a | PW | need-pdf |
| 24 | generatingeuphemiabids2026 | EUPHEMIA-compatible bids preprint 2026 | arXiv:2606.24183 | B18a | OA | need-pdf |
| 25 | euphemia-nemo | Current NEMO EUPHEMIA public description | (institutional) | B18a bid-count/format limits | OA | need-pdf |
| 26 | dolatabadi2025 | Dolatabadi et al. 2025 | arXiv:2510.14131 | B24 watch; method-similar group | OA | need-pdf |
| 27 | manzolli2024 | Manzolli et al. 2024, Energy | 10.1016/j.energy.2024.132497 | B22 baseline | PW | need-pdf |
| 28 | klein2023 | Klein & Schiffer 2023, Transp. Sci. | 10.1287/trsc.2022.0272 (arXiv:2201.03972) | B25 | OA | need-pdf |
| 29 | zhang2021 | Zhang, Wang, Qu 2021, TRE | 10.1016/j.tre.2021.102445 | B25 | PW | need-pdf |
| 30 | wu2021 | Wu, Lin, Liu, Jin 2021/22, TRB | 10.1016/j.trb.2021.11.007 | EVSP-side baseline | OA (White Rose preprint) | need-pdf |
| 31 | zhang2024 | Zhang et al. 2024, MICE | 10.1111/mice.13134 | EVSP-side baseline | PW | need-pdf |
| 32 | perdomo2020 | Perdomo, Zrnic, Mendler-Duenner, Hardt 2020 | (PMLR 119) | B11 | OA | need-pdf |
| 33 | hardt2022 | Hardt, Jagadeesan, Mendler-Duenner 2022 | (NeurIPS 2022) | B11 | OA | need-pdf |
| 34 | performative-survey | Dissecting Performative Prediction survey | 10.1145/3816429 | B11 framing | ? | need-pdf |
| 35 | dragotto2023 | Dragotto & Scatamacchia 2023, IJOC | 10.1287/ijoc.2022.0282 | B32 | OA (arXiv) | need-pdf |
| 36 | carvalho2023 | IPG tutorial, INFORMS TutORials | arXiv:2306.02817 | B32 orientation | OA | need-pdf |
| 37 | carvalho2025 | Cut-and-Play, Operations Research | 10.1287/opre.2023.0327 (arXiv:2111.05726) | B32 | OA | need-pdf |
| 38 | carvalho2024 | When Nash Meets Stackelberg, Mgmt. Sci. | 10.1287/mnsc.2022.03418 (arXiv:1910.06452) | B32 | OA | need-pdf |
| 39 | kleinert2021 | Kleinert, Labbe, Ljubic, Schmidt 2021 survey | 10.1016/j.ejco.2021.100007 | Direction A backbone | OA | need-pdf |
| 40 | fischetti2017 | Fischetti, Ljubic, Monaci, Sinnl 2017 | (Oper. Res. 65(6)) | Direction A backbone | PW | need-pdf |
| 41 | tahernejad2020 | Tahernejad, Ralphs, DeNegre 2020 (MibS) | (Math. Prog. Comp.) | Direction A backbone | OA | need-pdf |
| 42 | gvf2024 | Learning Generalized LP Value Functions, NeurIPS 2024 | (proceedings) | B31 | OA | need-pdf |
| 43 | fanzeres2020 | Fanzeres, Street, Pozo (CCG for Nash) | (citation to verify FIRST) | B32 prior art | ? | need-pdf |
| 44 | he2021 | He et al. 2021, Joule | 10.1016/j.joule.2020.12.005 | B24 economics | PW | need-pdf |
| 45 | crozier | Crozier et al. | arXiv:2311.11464 | B24 prior art | OA | need-pdf |
| 46 | sun2025 | Sun, Guo, Zhang, Jia 2025, Energy | 10.1016/j.energy.2025.135640 | B34 | PW | need-pdf |
| 47 | li2014 | Li, Wu, Oren 2014 | 10.1109/tpwrs.2013.2278952 | B15/B23 baseline | PW | need-pdf |
| 48 | liu-yin2025 | Liu & Yin 2025, Transp. Sci. | 10.1287/trsc.2023.0489 | original handoff request | PW | need-pdf |
| 49 | you2026 | You et al. 2026, Oper. Res. | 10.1287/opre.2023.0615 | original handoff request | PW | need-pdf |
| 50 | devivero2019 | De Vivero-Serrano, Bruninx, Delarue 2019 | 10.1016/j.apenergy.2019.113375 | original handoff request | PW | need-pdf |

## Context and deprioritized

Everything else encountered is catalogued in `papers.csv` with relevance
`domain-context` or `method-anchor`; pull items into this queue only when a
specific claim needs them. Deprioritized categories (unchanged from the
original handoff): additional heuristic DP/peel/greedy campaign literature;
generic MARL bidding surveys beyond what the audits cover.
