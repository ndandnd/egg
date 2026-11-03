# Transfer-campaign launch consistency review

The protocol and current runner agree on the frozen development split: only
new seeds 2018/2019 are materialized, with 20/28 services and fresh
case/market identities. Both remain `dev`, outside stage-2 training and prior
development. The prior 2004/2005 test seeds remain reserved; 2020/2021 are
recorded as future reservations without materializing their cases or labels.
The runner rejects overlap with prior profiles, reservations, and model
training groups. It loads the pinned stage-2 model and performs inference;
there is no fit or label update in this package.

The frozen order matches the protocol: four source cells first; then, for
each seed in order, five native target arms and two repair arms. That is 14
native cells and four repair cells. Their hard caps total
`14 × 100 + 4 × 240 = 2,360` seconds; the separate 45-second inference cap
brings the worst-case work to 2,405 seconds, below the 3,000-second controller
guard, 3,300-second shell timeout, and 3,600-second Slurm allocation. The
wrapper requests one CPU, 8 GB, and 60 minutes, excludes the named node, and
disables requeue. It records requested and allocated CPU fields.

The source/inference ordering is enforced in code: the inference gate requires
exactly the four source catalog rows and rejects any target launch receipt;
each target arm also requires an inference receipt. Proposals are generated
from those source rows and replay-checked before target work. Source plans and
their acquisition times, the one pre-target inference receipt, per-proposal
online timing, selection/direct-rescoring fields, target worker time, and
repair/hull phases are kept separate. For later fully paid online comparisons,
count the two source acquisitions once per timetable and the shared inference
process once; `source_paid_seconds` is repeated in each arm's selection
receipt, and `result.elapsed_seconds` already includes selection/lookup, so
those fields should not be added repeatedly or double-counted.

No budget, order, split, no-refit, or accounting inconsistency surfaced in
this pass. This is a source review only, not launch approval: the runner lists
`src/tests/test_transfer_campaign.py` among frozen source files, but that test
file was absent at review time. Until it is added, the source hash freeze
cannot complete. The implementation and focused test receipt are still under
finalization.


Root finalization: the focused transfer, historical stage-2 and route-repair
suite passed 14 tests. Wrapper syntax, frozen design (18 cells, two development
groups and four unmaterialized reservations), 31 unique source pins and diff
checks passed. Independent logic review found no further leakage, comparison
or resume issue. Before freezing, the implementation now saves direct-proposal
rescoring separately, uses a neutral source-fallback explanation, and salvages
replayed provisional plans when a later hull check fails. A failed prospective
inference remains receipted without retry; independent control arms continue,
while the projected learned arm requires a successful hash-checked proposal.
The shared learned repair uses the valid frozen model independently of that
source-fleet projection. Source and target lower bounds remain separate.
No native solve ran locally. This package is ready for one cluster launch at
its prospectively recorded budget; it is not a scientific result or ML claim.
