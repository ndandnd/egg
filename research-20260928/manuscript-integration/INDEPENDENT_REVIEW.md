# Independent core-manuscript consistency review

**Disposition:** no remaining mathematical or citation blocker found in the
reviewed core after the corrections listed below. This was a bounded
consistency pass, not a new numerical audit: I compared the assembled core
against `paper/manuscript.md` sections 3--6.2 and appendices A--B, and checked
the assembled `related_work.tex` against its cited keys and source map.

## Findings

- The complete-fleet support bound has the same direction as the historical
  proposition: own-price regret is at least the plan's excess cost over the
  complete-schedule hull, which is at least the planning gap. The equality
  characterization is conditioned on attainment, and the proof uses a
  physical planner minimizer. The quadratic upper bound's hypotheses and
  curvature-weighted feasible-load diameter are stated together.
- The two-service construction's physical costs, hull mixture and values
  agree with the historical derivation: $D=97$, $CH=7591/80$,
  $\Delta=169/80$, own-price regret $13$, and common-hull-price fleet/supply
  LOC of $0$ and $169/80$. The reserve/loss/connector example's rational
  values and the fixed-$K$ open-neighborhood qualification also agree.
- Replication correctly distinguishes one growing operator from separately
  reserved pair operators. The nearest-integer rule retains both choices at
  ties; the $n=40k+1$ whole-operator regret and vanishing gap formulas agree
  with the direct derivation. The $n=20$ planner tie retains regrets $7$ and
  $14$. The per-pair $20/n$ bound and its summed interpretation depend on the
  stated reserved connector rights.
- The related-work text now distinguishes uplift accounts from EGG's
  own-price regret, Shapley--Folkman aggregation context from the exact
  replication proof, fixed-schedule fleet counting from charging feasibility,
  and continuous EV charging coordination from discrete route support. Public
  data wording separates source reference bus parameters from EGG scenario
  assumptions; it retains the one-Hildenbrand-timetable/two-depot limit and
  makes no equal-quality speedup or learned-benefit claim. No first-ever claim
  or general pricing novelty claim appears in the reviewed core.
- Corrections made during this pass were followed by a final read: malformed
  duplicate commas in the replication and robust formulas were removed; the
  replication proof now compares the integer regimes explicitly; the
  $Q$-seminorm is defined; supply smoothness covers the feasible-load hull;
  supply notation is linked to market state; and Dantzig--Fulkerson is no
  longer cited for Dantzig--Wolfe/Fenchel certificates.

I found no unresolved core label or citation-key issue by inspection. The
review did not examine the computational chapter or public-case evidence,
rerun a solver, or access new data. Root reports that visual QA covered the
assembled 19-page document, five figures, and four tables.

## SHA-256 of reviewed inputs

| File | SHA-256 |
|---|---|
| `paper/latex/main.tex` | `5b712e159fe5de0f58d912db03f390394367a3f43a29e7a3f15e450e94aaa6fb` |
| `paper/latex/model_theory.tex` | `3771fedd157eef21fdc6468ff3cb7011794c5be928d56ce6e151b10e5a434f22` |
| `paper/latex/exact_results.tex` | `3c562d4015ae96a2b60bc9367a343126852001513528fb929f6475ed6c72b86c` |
| `paper/latex/proof_appendix.tex` | `af0f37fef0e7bbe6971f92d7461228df855f8d33895b8d37fa263b46b9e76e22` |
| `paper/latex/related_work.tex` | `3470d3e2215ce23252d5e8dd92cc90db7daf59788d85fb5082e9fa6e231010a7` |
| `paper/latex/references.bib` | `fc1b1c5c0ef0f35e5da2e5eafae2987eff64365432bed973e369899d2e8828fd` |
| `research-20260928/manuscript-integration/LITERATURE_SOURCE_MAP.md` | `c794da68bdd6207c3c767dea7233cf8f36b211d7f3a0f09ad8da2ae1fe5e30eb` |
