# Response to the focused theory review

All three requested corrections were applied only to the new focused paper.
No numerical work, import, compile, test, hash, old manuscript edit or commit
was performed. Compilation remains the parent's integration step.

1. framework.tex now says every **admissible attained maximizer** in the
   restricted-price support conclusion. The unrestricted zero-regret and
   subgradient statements remain separate. A short F(e)=|e|, singleton-plan
   example explains why containing one admissible dual maximizer does not
   make every dual maximizer admissible. The proof states the same distinction.
2. proofs.tex now correctly associates n=20, m=13 with regret7 and m=14
   with regret14. The body now records the association explicitly, rather
   than presenting the two values without their corresponding optima.
   The displayed general regret formula is unchanged.
3. ownership.tex explicitly reimplements every aggregate optimal projected
   outcome using m fixed-pair one-bus owners and n-m fixed-pair two-bus
   owners before comparing individual incentives. The corollary is limited
   to such a reserved-pair implementation. The proof explains why identical
   service copies and reserved connectors preserve aggregate loads, costs,
   prices and the projected response comparison. It does not assign fixed
   ownership to an arbitrary literal cross-matched aggregate schedule.

The main narrative was reread for scope and coherence without repeating the
full proof audit. Its central question remains the fixed posted own-load
tariff for one complete fleet; classical support machinery, unchanged-resource
movement stability, changed-equipment erasure and reserved ownership are
distinguished. One introductory phrase now says when the fleet purchases
energy, avoiding the ambiguous phrase about energy availability to supply.

Public optimal-fleet support remains explicitly unresolved at the existing
exact bounds. The draft retains the independent review's significance bar:
low-dimensional exact results and dominated-movement stability can be correct
yet too modest; internal exact agreement establishes neither novelty nor
operational relevance. The closest Wu2019 formulation remains a fulltext
positioning gap. These corrections do not establish submission readiness.
