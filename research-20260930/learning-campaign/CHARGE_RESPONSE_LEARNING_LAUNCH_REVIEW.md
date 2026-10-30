# Charge-response learning launch review

Reviewed prospectively on 30 September 2026. The completed charging comparison
motivates learning the cost of a stored source fleet after the pinned charging
procedure, rather than treating its inherited charging schedule as route quality.
This is an exploratory source selector, not a new route generator.

The ten new synthetic groups stay separate: six training groups (2022–2027,
two each at 12/20/28 services) and four development groups (2028–2031, two each
at 20/28 services). Reserved 2004/2005/2020/2021 are not materialized. Twenty
source acquisitions precede twelve training charging labels. All six pairs must
have replayed labels before fitting; missing labels cause a recorded model
failure while independent development controls continue. No label is silently
dropped to shrink the training design.

The fixed ridge model predicts per-trip cost change from pre-target source-plan
features. Scaling uses training rows only. There is no tuning or development
refit. All four development choices are written and hashed before any development
charging or cold outcome. Eight development charging cells and four cold controls
then provide the comparison. The frozen EdgePrior baseline uses its original
topology projection and complete tie rule, not score alone.

The primary comparison is paired excess nonlinear cost over the paid best of two
charged candidates, with feasibility and actual paid time. This is not regret
relative to a global optimum. Linear-optimal charging schedules can have different
nonlinear costs; the label describes this pinned procedure. Source acquisition,
training/inference, one chosen charging child, and both children for best-of-two
comparison are distinct costs. Feasible uncertified and interrupted results keep
their status, physical replay, provenance and all spent time.

Bounded independent reviews checked model features, training-only normalization,
residual reconstruction, source lineage and prediction order, and continuation
after failed inference. They also checked the old baseline's semantics and the
six-pair coverage rule; both identified issues were corrected before launch.
Root reviewed the final guard implementations and resource order.

Validation completed before launch: eight focused pure/mocked tests passed,
covering split/order, complete training coverage, train-only fitting, the old
projection rule, premature development outcomes, failed-inference resume, and
resource/source scope. Wrapper syntax, pure design generation, and diff checks
passed. The execution pins 23 source files and three archived old-model inputs.
No local native optimization or extra qualification campaign was run.

Prospective resource ceiling: 44 children at 100 seconds each plus one 60-second
fit/inference call (4460 seconds in total), controller 5400, shell 5700,
Slurm 6000 seconds. One requested CPU, 8 GB, one native/BLAS thread, no requeue,
exclude scaglione-compute-01. Actual allocated CPUs will be recorded separately.
The launch guard refuses another active EGG job or an existing destination
checkout. Ready for one submission after the reviewed execution source is
committed and pushed. Results remain pending review.
