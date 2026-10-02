# Scoped research continuation — ends 2 October 2026 at 13:00 America/New_York

Deadline: 2026-10-02T17:00:00Z. User authorized literature/theory/research-design work until then. This does not restart the older paused cluster/research automations.

## Scope
- Work only on branch `codex/sota-review-20261002`, worktree `/Users/nadan/Documents/ChatGPT/egg/sota-review-20261002`, based on Claude handoff commit `c560378adc84ef010afe5c4b1bfce0408dd1704b`.
- No cluster SSH, submissions, monitoring, solver/training experiments or edits to `claude/research-20261001`. Claude retains cluster ownership through its stated17:45UTC wrap-up. No sealed DEV/TEST/A6/B3/confirmation/GIRO access.
- Six historical log entries already appended verbatim and verified. `GOOGLE_DOC_APPEND_RECEIPT.json` is authoritative. Do not append again or silently revise their scientific claims.
- Requested main deliverable: `SOTA_REVIEW.md`, addressing all six questions in Section5 of `doc/GPT_HANDOFF_20261002.md`, primary-source verification and top5 prospective experiments with hours/CPUh/stop-go. Source notes may support the report.
- User wants Operations Research quality; assess novelty and proof/empirical requirements candidly. Do not equate an ambitious target with acceptance readiness.

## Current work (updated 05:30 UTC)
- Main `SOTA_REVIEW.md` is drafted: six requested topics, ranked five experiments, explicit engineering/CPU estimates, failure-aware controls, contribution map and do-not-pursue list. It is a research review, not a completed journal paper.
- Three Sol6.1 literature reviews, a Sol6.1 mathematical challenge and adversarial positioning review are complete. Luna Max checked consistency; root incorporated the material fixes. No other initial agents remain active. Check workers before duplicating.
- The Sol6.1 package `/root/joint_price_certificate_research` is complete; root reviewed and integrated `notes/JOINT_PRICE_BOUND_REVIEW.md`. Joint lower-bound reuse dominates separate reuse, with a strict hand example; mixture equality needs a convex outer load set. The outer cost/load model also bounds the hull from below. Direct Geoffrion–Nauss1977 concave-envelope prior art prevents a generic novelty claim. No active review agents remain as of this checkpoint.
- Gerbaux/Desaulniers/Cappart 2025 COR173:106848 DOI10.1016/j.cor.2024.106848 already does incumbent-imitation GNN/greedy arc reduction and incoming/outgoing per-trip top-m (Algorithm2) at hundreds/thousands of trips. Full published primary PDF inspected. Plain learned bus pruning/top-m is not novel.
- Sugishita/Grothey/McKinnon2024 IJOC36(4):1129–1146 DOI10.1287/ijoc.2022.0140 already learns dual warmstarts for CG. Do not claim generic ML+CG novelty.
- Final ICML2024 ConPaS PDF access issue resolved by downloading publisher GitHub asset into untracked `tmp/`; final methods/experiments inspected and source note updated. No need to retry access.
- Core certificate caveats incorporated: unrestricted/global lower bounds only; subtract an upper conjugate enclosure; check domains, original physical set and nonnegative certificate width; cached cost/load definitions must match.
- Main rank-3 proposed comparison now includes an unseeded full-pricing control at equal end-to-end allowance; prospective estimate45–55CPUh supersedes narrower oracle-only note estimate. No launch authorized in this scope.
- The aggregate structure package is complete: `FLEET_LOAD_OUTER_RELAXATION.md` derives conditional stock/interval/occupancy constraints with endogenous fleet count; `AGGREGATE_LOAD_PRIOR_ART.md` checks five primary sources and inner/outer/exact directions; `BOUND_DOMAIN_COMPARISON.md` adds de Vos2024's optimistic/conservative network precedent and price-dependent objective mapping. All are integrated into the main review. Root reviewed algebra and corrected the aggregation counterexample to account for tight individual power lower bounds.
- A mandatory-energy facet strengthens a hand-derived joint price bound from0.5to1. This is a mathematical illustration, not measured performance. Conservation cuts implied by the full LP cannot strengthen its exact projection by themselves; integer-oracle certificate cuts may cut off full-LP points. No blanket comparison is justified. Exact fixed-window aggregation and virtual batteries are prior art, not a novelty claim for EGG.

## Subsequent bounded packages, in order
1. Turn the highest-value numerical-reliability and matched-budget oracle comparisons into concrete prospective protocols with artifact fields, timing, baselines and rejection criteria. Use the now-explicit main report budgets. No execution; do not expand into a new training campaign. Treat the new aggregate/cached model as an optional separate ablation requiring an EGG assumption/mapping check, not a silently added arm.
2. Address a material source/theory gap only if it can change a recommendation. The joint-price/aggregate-energy derivations and novelty checks are already complete; do not redo them as new work. Avoid repeated audits, broad rereads and generic expansion. Before deadline prepare the final concise verdict on established evidence, possible novelty and missing work.

First milestone `94fe76dc` is pushed to `origin/codex/sota-review-20261002`; subsequent commits on the same branch carry follow-up findings. All tracked changes are under `research-20261002/sota-review/`. The local `tmp/` directory contains scratch reads/downloads only and must not be committed. Claude's branch remains at `c560378adc84ef010afe5c4b1bfce0408dd1704b` from this task's perspective; never reset or overwrite any newer Claude work.

At or after17:00UTC: no new research package; record final state, back up completed artifacts and delete the scoped review automation. Report the final deliverable. Do not resume cluster work or old schedules. Before that time notify only significant findings or material blockers; keep routine follow-up quiet.

Scoped automation created: `egg-literature-review-until-1-p-m`, hourly at minute00 through2026-10-02T17:00:00Z. The old EGG campaign automation remains paused; unrelated project schedules are outside this task.
