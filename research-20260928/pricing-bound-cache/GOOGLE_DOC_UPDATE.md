# Pricing-bound reuse implemented — 28 September 2026

The saved-pricing-bound lead now has an explicit opt-in implementation. It retains physical pricing bounds with their original prices and source identities, then recomputes the electricity-cost conjugate for the target market. Bound reuse is a separate control from feasible-plan reuse. The completed pilot and its recorded outcomes are unchanged.

A successful fresh target pricing call is still required before numerical certification. Incompatible cache inputs and contradictory lower/upper enclosures fail explicitly, including when a work limit prevents fresh pricing. Cache validation and re-evaluation count against the target time budget. Source computation costs remain visible, while unmeasured child and preparation costs remain marked as unknown for the future experiment runner.

The focused new-cache and existing feasible-reuse tests passed all 26 checks, and independent review found no remaining mathematical or admission blocker. This is implementation progress; online performance has not yet been measured. The next step is the numerical restricted-master integration, followed by a new frozen comparison against the existing baselines. No new cluster experiment was launched in this package.

Implementation and scientific scope: https://github.com/ndandnd/egg/blob/8a54521b92c518aa999c6f18a915eca2ffdc8e21/research-20260928/pricing-bound-cache/README.md
