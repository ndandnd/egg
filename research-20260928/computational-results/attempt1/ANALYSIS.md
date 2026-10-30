# First computational DEVELOPMENT screen

All 32 stages accounted: {'certified': 10, 'bounded': 10, 'budget_exhausted': 9, 'ineligible': 3}. The two public depots share one base timetable.
The 6 launched public hull stages used one master and two pricing requests each; recorded native pricing wall was 172.81–173.20 s of roughly 184 s child wall, while polishing took under 0.006 s per stage. Native pricing is the measured runtime bottleneck. Separately, omitting a final master leaves useful mixture improvements unrealized; the master itself is inexpensive. Shifted retained public stages were ineligible because initial retained bounds were not certified. The multivisit shifted cold hull instead stopped at the rational projected-bit limit; that is a separate arithmetic issue.
Posthoc two-column replay below can improve a saved feasible upper bound, but its time and quality are not credited to the frozen run. A prospective change could reserve time for a final restricted master and test replayed feasible-pool reuse; native pricing warm starts also merit matched development comparison. No change is claimed effective yet.

Whole Slurm elapsed: 2157.00 s; supervisor elapsed: 2136.29 s. Raw manifest SHA-256: `78d642e204143a05938a19fc447791178ae7890f5a01a8e05a179e73f6eab160`; source `e39bc7e31ea21dae64365c31fa88a85e4b0de349`.

| Case | Market | Stage | Outcome | Child wall s | Lower | Upper | Pricing | Master | Polish s |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Cyclic | Initial | Planner | certified | 2.74 | ≈97.0000 | ≈97.0000 | — | — | — |
| Cyclic | Initial | Cold hull | certified | 2.73 | ≈94.8875 | ≈94.8875 | 3 | 2 | 0.013 |
| Cyclic | Initial | Retained hull | certified | 2.78 | ≈94.8875 | ≈94.8875 | 3 | 2 | 0.012 |
| Cyclic | Initial | Own-price | certified | 2.63 | ≈134.0000 | ≈134.0000 | — | — | — |
| Cyclic | Shifted | Planner | certified | 2.68 | ≈99.0000 | ≈99.0000 | — | — | — |
| Cyclic | Shifted | Cold hull | certified | 2.84 | ≈97.9875 | ≈97.9875 | 3 | 2 | 0.013 |
| Cyclic | Shifted | Retained hull | certified | 2.68 | ≈97.9875 | ≈97.9875 | 1 | 1 | 0.008 |
| Cyclic | Shifted | Own-price | certified | 2.68 | ≈140.0000 | ≈140.0000 | — | — | — |
| Multivisit | Initial | Planner | bounded | 2.83 | ≈84.4543 | ≈84.4690 | — | — | — |
| Multivisit | Initial | Cold hull | budget_exhausted | 3.04 | ≈80.3961 | ≈84.4681 | 4 | 4 | 0.033 |
| Multivisit | Initial | Retained hull | budget_exhausted | 2.99 | ≈80.3961 | ≈84.4681 | 4 | 4 | 0.033 |
| Multivisit | Initial | Own-price | certified | 2.68 | ≈124.2604 | ≈124.2604 | — | — | — |
| Multivisit | Shifted | Planner | bounded | 2.89 | ≈84.7134 | ≈84.7216 | — | — | — |
| Multivisit | Shifted | Cold hull | budget_exhausted | 3.18 | ≈81.1732 | ≈86.0446 | 3 | 3 | 0.236 |
| Multivisit | Shifted | Retained hull | ineligible | — | — | — | — | — | — |
| Multivisit | Shifted | Own-price | certified | 2.83 | ≈124.5130 | ≈124.5130 | — | — | — |
| Hildenbrand D15 | Initial | Planner | bounded | 182.91 | ≈408.5331 | ≈547.6039 | — | — | — |
| Hildenbrand D15 | Initial | Cold hull | budget_exhausted | 184.49 | ≈408.5331 | ≈552.3589 | 2 | 1 | 0.005 |
| Hildenbrand D15 | Initial | Retained hull | budget_exhausted | 184.50 | ≈408.5331 | ≈552.3589 | 2 | 1 | 0.004 |
| Hildenbrand D15 | Initial | Own-price | bounded | 63.12 | ≈337.7309 | ≈413.3520 | — | — | — |
| Hildenbrand D15 | Shifted | Planner | bounded | 183.04 | ≈339.3535 | ≈517.3270 | — | — | — |
| Hildenbrand D15 | Shifted | Cold hull | budget_exhausted | 184.39 | ≈339.3535 | ≈547.4646 | 2 | 1 | 0.005 |
| Hildenbrand D15 | Shifted | Retained hull | ineligible | — | — | — | — | — | — |
| Hildenbrand D15 | Shifted | Own-price | bounded | 63.05 | ≈379.4143 | ≈424.0617 | — | — | — |
| Hildenbrand D16 | Initial | Planner | bounded | 182.88 | ≈423.1551 | ≈530.6589 | — | — | — |
| Hildenbrand D16 | Initial | Cold hull | budget_exhausted | 184.22 | ≈423.1551 | ≈530.6589 | 2 | 1 | 0.005 |
| Hildenbrand D16 | Initial | Retained hull | budget_exhausted | 184.23 | ≈423.1551 | ≈530.6589 | 2 | 1 | 0.006 |
| Hildenbrand D16 | Initial | Own-price | bounded | 62.92 | ≈405.9497 | ≈433.7461 | — | — | — |
| Hildenbrand D16 | Shifted | Planner | bounded | 182.88 | ≈377.6599 | ≈547.8787 | — | — | — |
| Hildenbrand D16 | Shifted | Cold hull | budget_exhausted | 184.19 | ≈377.6599 | ≈549.6996 | 2 | 1 | 0.005 |
| Hildenbrand D16 | Shifted | Retained hull | ineligible | — | — | — | — | — | — |
| Hildenbrand D16 | Shifted | Own-price | bounded | 62.90 | ≈377.6599 | ≈430.8594 | — | — | — |

Two-state hull times include each arm's initial state:

| Case | Arm | Initial s | Shifted s | Total s | Outcomes |
| --- | --- | ---: | ---: | ---: | --- |
| Cyclic | Cold hull | 2.73 | 2.84 | 5.57 | certified, certified |
| Cyclic | Retained hull | 2.78 | 2.68 | 5.46 | certified, certified |
| Multivisit | Cold hull | 3.04 | 3.18 | 6.22 | budget_exhausted, budget_exhausted |
| Multivisit | Retained hull | 2.99 | — | — | budget_exhausted, ineligible |
| Hildenbrand D15 | Cold hull | 184.49 | 184.39 | 368.88 | budget_exhausted, budget_exhausted |
| Hildenbrand D15 | Retained hull | 184.50 | — | — | budget_exhausted, ineligible |
| Hildenbrand D16 | Cold hull | 184.22 | 184.19 | 368.41 | budget_exhausted, budget_exhausted |
| Hildenbrand D16 | Retained hull | 184.23 | — | — | budget_exhausted, ineligible |

Posthoc exact stored-float two-column public cold-pool replay (outside the baseline budget):

| Case | Market | Saved upper | Posthoc upper | Improvement | Second-column weight | Replay s |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Hildenbrand D15 | Initial | ≈552.3589 | ≈482.9732 | ≈69.3857 | ≈0.4824 | 0.088 |
| Hildenbrand D15 | Shifted | ≈547.4646 | ≈492.2125 | ≈55.2521 | ≈0.4552 | 0.095 |
| Hildenbrand D16 | Initial | ≈530.6589 | ≈493.2768 | ≈37.3821 | ≈0.3657 | 0.083 |
| Hildenbrand D16 | Shifted | ≈549.6996 | ≈510.1317 | ≈39.5679 | ≈0.3674 | 0.094 |

Posthoc timing covers raw pool read/hash, column replay, closed form and exact mixture; it excludes imports, frozen-case construction and report/figure writing. The mixture is a convex-hull object, not one operational fleet schedule.
The figures show descriptive native numerical evidence, not exact ideal-model bounds. Missing component timing is unknown, not zero. Outcomes and quality must be matched before any retained-versus-cold speed claim.
