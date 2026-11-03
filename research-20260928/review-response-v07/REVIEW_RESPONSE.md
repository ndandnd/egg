# Selective response to the external v0.6 review

The review is strong on the mismatch between the paper's economic question and
its computational presentation. Its missing analytical baseline is a substantive
correction, not cosmetic editing. The cap dependence and unobserved start
acceptance also materially limit interpretation. Its categorical journal
predictions and proposed split are judgments, not established requirements.

| Review point | Decision and action |
| --- | --- |
| Main computations report CH without D, gap or regret | Accept. Reconstruct a compact joint table from the existing reviewed screen. Regret is evaluated at the specific returned planner incumbent, not an unknown optimum. |
| Analytical bound beats computed lowers | Accept after independent derivation for both depot cases and markets. Report exact ideal-model floors separately from native numerical bounds. The proposed native-flat-derived improvement is excluded from the exact floor; it would retain its model/tolerance qualification. No new solver evidence is claimed. |
| Reuse success depends on four-call/4096-bit limits | Accept the observed confounding. Move the historical comparison out of the main paper. Reject the untested assertion that cold solving must certify in seconds at sixteen calls. |
| No-incumbent bug | Agree it invalidates a clean performance comparison. The repair already exists with independent tests; do not duplicate the repair or overwrite failed outcomes. New runs would be separate experiments. |
| Submitted starts not known to be accepted; one seed | Accept the limitation, remove from main. Neither benefit nor pure noise is established. Logging acceptance and repeated seeds belong in a future controlled design; five seeds is not a universal sufficiency rule. |
| Old damping study | Defer. It uses a different terminal rule and is outside the evidence admitted here. Cycling alone does not prove nonexistence of a supporting plan or the necessity of a particular hull algorithm. No old raw outcomes were used. |
| Missing antecedents | Restore Andrianesis, Madani and Hümbs with primary-source checks. No learned-method claim is made; future learned-column-generation work should be cited when that method is evaluated. |
| Scale and independent timetables | Agree. Two depots remain one public timetable. Preserve the computational research objective and grouped evaluation plan. Eberbach intake already exists, without comparative outcomes. |
| Split into two papers / venue prescription | Do not decide from this review alone. Refocus the present manuscript and separate the development record; keep the broader computational-paper objective active. |
| Presentation | Align Eq. 1, distinguish feasible-set symbol from supply cost, remove capped-time and uncontrolled-start figures from the main paper, and make the abstract report the actual findings. |

## What this revision does not establish

It does not close a public nonconvexity gap, demonstrate acceleration, create
independent network replications or train a predictor. Analytical postprocessing
is not credited as a timed result of an earlier algorithm. Native numbers do not
become ideal rational-model proofs because their stored floats are processed
with exact arithmetic. The unchanged development record preserves unsuccessful
attempts and all recorded computation. No new cluster allocation or solver run
was used for these manuscript corrections.

## Next research step

Integrate the valid analytic baseline into the reporting/coordinator with explicit
model scope, then size a bounded diagnostic before freezing any new comparison.
The frozen retrieval launch's pending replacement decision remains separate;
no rerun or protocol change was made in this revision. Scale and equal-quality
comparisons, with D/CH/regret and repeated seeds where appropriate, take priority
over another overlapping pilot or immediate ML training.

## Supporting records

- Analytic bounds and reconstructed incumbent regret: `analytic-bounds/DERIVATION.md`, `compute_bounds.py`, `bounds.json`.
- Historical no-incumbent repair and its independent tests: `../no-plan-repair/README.md` (156 focused tests and independent review; historical failures unchanged).
- Cap evidence: `../feasible-pool-pilot/results-attempt1/analysis/README.md`; source configuration in `src/experiments/retrieval_comparison.py`.
- Unconfirmed native starts: `../pricing-start-pilot/results-attempt1/`.
- Three restored primary literature records and scope: `LITERATURE.md`.
- The historical computational source is preserved byte-for-byte: `paper/latex/computational_results.tex`, SHA-256 `50fda5437632c7286bff016df8c688e7d9a0e5b54896393e271d62834913ffdb`.

## Additional improvement from combining existing evidence

The same-screen own-price response provides another hull lower bound,
`V_lower(p) - F*(p)`. For the three-service multivisit case this improves the
changed-market hull floor to 84.622956 and narrows the planning-gap interval
to [0, 0.10] under native numerical qualifications. The table also uses a
physical feasible upper as a hull upper and a hull lower as a physical lower.
This is analytical postprocessing of existing evidence, with no runtime or
reuse-effect claim. It is distinct from the exact ideal energy floors for the
public cases.
