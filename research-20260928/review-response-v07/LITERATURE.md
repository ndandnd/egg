# Literature correction for Claude review item 7

This bounded correction restores three direct price-support antecedents in the LaTeX bibliography and related-work section. The references are cited for the methods and scopes stated in their sources; none establishes the manuscript's fleet-specific replication result or own-price regret test.

## Restored references and source checks

| Key | Verified primary record and metadata | What the source supports | Boundary kept in the manuscript |
| --- | --- | --- | --- |
| `madani2018pricing` | [arXiv:1804.00048v1](https://arxiv.org/abs/1804.00048v1), submitted 30 March 2018; Mehdi Madani, Carlos Ruiz, Sauleh Siddiqui, and Mathieu Van Vyve. The arXiv primary record gives the title and authors. | Compares convex-hull, integer-programming, and European-style day-ahead pricing in a Power Exchange setting with nonconvex demand bids; the abstract describes efficient computation of convex-hull prices using continuous relaxations for certain products. | This is an arXiv preprint, not evidence about bus schedules or the manuscript's own-price best-response proposition. The LaTeX entry labels it a version-1 preprint. |
| `andrianesis2022hull` | [Author manuscript, arXiv:2012.13331v2](https://arxiv.org/abs/2012.13331v2), revised 24 October 2021; Panagiotis Andrianesis, Dimitris Bertsimas, Michael C. Caramanis, and William W. Hogan. The existing bibliography records the journal version as *IEEE Transactions on Power Systems* 37(4), 2578–2589 (2022), DOI [10.1109/TPWRS.2021.3122000](https://doi.org/10.1109/TPWRS.2021.3122000). | The author abstract describes Dantzig–Wolfe decomposition and column generation as an exact, finitely convergent approach to convex-hull price computation in nonconvex electricity markets. | It is a direct convex-hull pricing antecedent. The paper does not claim that this manuscript uses their algorithm or that its bus-feasibility columns are the same objects as electricity-market participant schedules. The DOI landing page was not readable through the browser in this check; title, author list, version, and method were verified on the primary author manuscript. |
| `huembs2022complete` | [Springer version of record](https://link.springer.com/article/10.1007/s00186-022-00775-z), published 26 March 2022; Lukas Hümbs, Alexander Martin, and Lars Schewe, *Mathematical Methods of Operations Research* 95, 451–474, DOI [10.1007/s00186-022-00775-z](https://doi.org/10.1007/s00186-022-00775-z). | Gives necessary and sufficient conditions for linear prices supporting competitive equilibrium in decentralized market problems with integral decisions and complete linear feasible-set descriptions; the article's examples show that formulation matters. | The cited result concerns the stated decentralized linear/MILP setting. It does not imply price support for EGG's modeled fleet schedules or settle the separate convex-cost best-response calculation. |

The existing related-work paragraph preserves the distinctions among uplift and nonconvex pricing, convex-hull pricing, and the manuscript's conditional own-price regret. The new text does not make a novelty claim that convex-hull pricing or price-support analysis is new.

## Review items deliberately not added

The review also asks for Bichler, Knörr, and Maldonado's demand-response pricing paper. It is a related, but more specialized, treatment of demand response and nonconvex-market pricing; this correction is capped at three additions, and that paper is not needed to substantiate the manuscript's claims. It remains an optional citation if the discussion is later expanded specifically to demand-response pricing or make-whole design. No learned-column-generation citation such as Morabit et al. was added: the current manuscript does not present a learned method. That reference is relevant only if a future version contributes or evaluates learned pricing/column-generation proposals.

The review's predictions that a journal “would reject” the paper or that particular changes are mandatory are editorial judgments, not established publication criteria. They are not presented as facts in the manuscript. The LaTeX related-work section instead reports the current study limits directly, including that it establishes neither an equal-quality speedup nor a learned-proposal benefit.

## Files changed

- `paper/latex/related_work.tex`: restored citations and tightened wording; all citations in this section resolve to a key in the LaTeX bibliography.
- `paper/latex/references.bib`: appended the three entries above; the pre-existing core entries were retained.
