# Launch verification

Root ran the two focused campaign/learner test modules together: ten tests
passed. The Slurm wrapper passed Bash syntax checking and git diff whitespace
checking. These checks do not perform native optimization. They cover independent
base-group splits, reserved-test exclusion, append-only catalog behavior, failure
time preservation, learner target-label isolation, immutable training receipts,
nonlinear cheapest-plan selection, and withholding bounds after failed replay. The last control uses the full target
objective rather than the older retrieval helper's linear billing objective.

Sol implemented the runner and model in separate bounded work packages. Luna's
independent launch review is recorded alongside this file. Root will pin and
publish the execution commit before submitting one isolated Slurm job. Native
model feasibility, runtime behavior and learning value are measured by that job;
no local check is treated as proof of a computational result.

The independent review found that raw native bounds could enter catalog bound
fields after an assessment failure. Root added explicit replay gating, preserved
unverified raw values separately, and added a focused regression before launch.
