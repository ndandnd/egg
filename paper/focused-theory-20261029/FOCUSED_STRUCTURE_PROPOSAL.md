# A focused first-draft structure

Editorial proposal only. Read current main/input headings and CRITICAL_RESEARCH_REVIEW04; no manuscript, consumed sources or evidence were changed. No compilation, numerical work, raw data, new literature or agents. Page estimates below are editorial estimates, not measurements from a new rendering.

## Decision

Compress and reorder. The body should answer two questions: **what exact assignment-dependent frontier can be derived under common-window charging, including common losses; and does a certified obstruction also occur in one richer declared timetable model?** Equipment, nominal phase diagrams and ownership replication explain consequences but currently receive too much independent narrative weight. Preserve their complete statements/proofs in appendices, with short body consequences and explicit pointers.

Do not force an ICML page limit or invent an ML contribution. A readable theory first draft can have substantial appendices. The current roughly26-page body can plausibly lose7–10 pages without removing a principal result or assumption, aiming for roughly16–19 body pages rather than an arbitrary conference format. Keep the exact physical model and public-certificate scope visible even if this costs a page.

## Concrete body order and content

1. **Introduction**: shorten the abstract and opening contribution roadmap around the common-loss finite efficient frontier, lossless support classification and declared public existence certificate. One sentence each for equipment and ownership consequences; remove their separate paragraph-long previews. Do not promise general scheduling tractability, calibrated relevance or a learning contribution.
2. **Complete fleets and support** (`framework.tex`): retain definitions of D,CH,V,weak support, complete-fleet participant and price qualification. Keep the classical criterion and one short explanation of its relevance. Move the detailed admissibility example to its existing proof appendix if needed; retain the actual admissible-price quantifier in the body theorem.
3. **Assignment-dependent common-window frontiers**: use the charge-only theorem as an accessible baseline, followed directly by signed lossless charging and the common-loss result. This is a single intellectual arc, even if retained as three numbered sections for easy implementation.
   - `heterogeneous.tex`: retain exhaustive graph/singleton/resource assumptions, r_m, exact projection and support criterion, plus the small heterogeneous worked frontier. Move the sorted complete-graph corollary proof discussion, detailed qualification counts and adequate-resource contrast to the appendix/evidence section. Keep a sentence that arbitrary allowed graphs use actual matching minima, not the sorted shortcut.
   - `v2g.tex`: keep explicit same-price signed settlement, assigned/paid-idle interpretation, gross connector use, minimum-gross lemma, thresholds and support criterion. Retain concise persistence/restoration statements as an illustration. Move the inline “Why the projection is exact” proof block and the full idle proof to a new appendix source. The theorem assumptions stay in the body; proof movement must not turn gross throughput into a net-load constraint.
   - `lossy.tex`: retain the accounting identity, fixed-matching lemma, threshold formula, finite segment theorem and its planning/support consequence. This is the most useful extension to foreground. Keep monotone-economics, negative-price/tie, cycle/full-projection and capped-idle limitations next to the claims. The existing `\LossyProjectionProofs` macro already places full proofs in the appendix. A short explanatory diagram is optional later; another numerical example is unnecessary.
4. **One public declared-model existence certificate** (`public_case.tex`): present the latest accepted D interval/gap certificate first, then the finite-mode opportunity set and synthetic assumptions, then a concise model-to-certificate/fleet-count argument. Retain fixed graph/timing/window restrictions and the distinction between physical D and unrestricted hull components. Keep the fee-stability consequence in one paragraph with its exact inequality/reference. Retained-evidence verification and the fresh solver-free same-host CLI provide the short reproducibility close. Do not reproduce the full failed-stage chronology in the body; preserve it in `certificates.tex`/the evidence map.
5. **Consequences and limits**, replacing most of the current separate construction/expansion/ownership bodies: approximately one page total. A paragraph explains that extra battery capability may erase support failure but a plan cheaper than the old hull is insufficient. A second distinguishes vanishing planning gap from whole-owner absolute regret, and states the uniform curvature/diameter bound with a pointer to complete replication details. A third records scope limits. Keep reserved-rights assumptions explicit whenever mentioning individual operators.
6. **Short conclusion and evidence statement**: one nonrepetitive close. Move long implementation case/negative-control denominators into an appendix evidence table and preserve their exact qualification scope. State internal author-run verification versus external replication and unresolved redistribution rights once, clearly.

Related work can follow the introduction or model, but should be condensed around the already inspected closest operational, aggregation, lossy-storage and classical-support comparisons. Retain citations/qualifiers; move any longer comparison discussion to a literature appendix if necessary. The compact contribution comparison table can remain. Do not distribute the same self-assessment and limitations across the abstract, each theorem, conclusion and evidence section.

## Dependency-safe source/input map

The lowest-risk first implementation keeps core inputs in their current logical order:

    body:
      related_work                 [shortened, same attributions]
      framework                    [core definitions/criterion]
      heterogeneous                [shared model/projection + one example]
      v2g                          [statements/short consequences only]
      lossy                        [statements + algorithmic consequence]
      public_case                  [latest accepted bounds + model + certificate]
      consequences                 [NEW concise summaries/pointers]
      implications/conclusion/evidence [shortened, no duplication]

    after \appendix:
      adequate_resources           [separate n-connector policy, unchanged]
      construction                 [MOVED full nominal/fee/reserve statements]
      expansion                    [MOVED full equipment/movement statements]
      ownership                    [MOVED full replication/regret statements]
      heterogeneous_proofs         [all shared/sorted/allowed-graph proofs]
      v2g_proofs                   [NEW extraction of current inline proofs]
      proofs                       [existing classical/nominal/expansion/replication proofs]
      certificates                 [numeric algebra + full retained failure history]
      \LossyProjectionProofs       [existing macro, defined by body lossy input]
      evidence_details             [optional extraction of qualification counts/chain]
      bibliography                 [or retain existing final placement]

This preserves original construction→expansion→ownership order, so the nominal model and equipment definitions appear before their appendix dependents. Forward references from the new body consequences are legitimate. Keep ALL existing theorem/section/figure labels when moving blocks; do not create duplicate labels or duplicate theorem statements. Numbering will change automatically. The portable evidence and consumed research artifacts are not reorganized.

The V2G proofs must be EXTRACTED, not merely omitted: include lemma/theorem/corollary proofs plus paid-idle proof in v2g_proofs. Give the paid-idle proposition a label if a body summary replaces its full statement. Avoid copying its statement into two theorem environments. Leave the common-loss macro defined in body lossy.tex and invoke it only after the appendix switch, exactly once. Existing proofs.tex is monolithic but can remain as-is initially: it already contains all classical, nominal, equipment and replication proofs, so moving their statements creates no missing proof dependency.

Before deleting any current body paragraph, classify it as definition/assumption, result, proof, evidence or interpretation. Move assumptions with their theorem, proofs with their appendix labels, and evidence with its immutable provenance references. Only repeated interpretation/roadmap prose should actually be removed. A sentence saying “same model” cannot replace the public case's finite-mode scope or the lossy theorem's monotonicity conditions.

## What can leave the body without weakening the main contribution

| Current material | Keep in main | Preserve in appendix |
|---|---|---|
| Nominal two-service construction/connector-fee phase diagram | One sentence locating the accessible specialization, or one compact example if the heterogeneous example is shortened | Full construction.tex, figures, continuous domain/boundaries and reserve/loss neighborhood |
| Expansion/equipment theory | Added options can preserve or erase failure; cheaper-than-old-hull is insufficient | All exact regions, mixed equipment accounting and movement dominance proof |
| Ownership replication | Participant definition; uniform-controls regret consequence; warning about absolute aggregate regret | Full scaling family, tied m values, reserved-pair reimplementation and proofs |
| V2G proof exposition | Physical model, gross lemma statement, thresholds, idle scope, short persistence/restoration example | All constructive proofs and exact example arithmetic |
| Numerical failure history/qualification counts | Latest accepted claim, fresh portable CLI status and exact scope of internal checking | Full history, all old failures/costs, denominators, manifests and certificate index |

The public result does not logically depend on the nominal/equipment/replication family. It uses framework support plus its separate declared-model certificate. The lossy frontier depends on the shared two-batch model and signed accounting, not on the nominal phase diagram. Those are the reasons this reordering is safe.

## Editorial priority

Do the source moves and summaries first, then compile/check every reference and visual once. Do not use compression as an excuse for a new proof or computation campaign. A focused first draft should be easy to describe in three sentences: an explicit assignment-dependent frontier; its price-support consequences; and a separately certified declared-timetable obstruction with inspectable retained evidence. Exact special cases and ownership refinements remain available to readers who need them.
