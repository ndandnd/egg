# Learning campaign first allocation

Commit the runner, Slurm wrapper, tests, and these documents. On the cluster,
submit from the reviewed clean checkout with `EGG_RUN_COMMIT` set to that
commit. The wrapper freezes a new attempt or resumes the same attempt after
checking commit, source hashes, runtime, native backend, and full design.
It writes one wrapper receipt per Slurm job ID. The controller appends
`catalog.jsonl` after each child receipt, runs a 45-second bounded trainer
before development target solving, and writes `summary.json` after all
17 native cells are accounted for.

Pure local check (no solver):

```sh
PYTHONPATH=src python3 -m unittest src.tests.test_learning_campaign
```

The `design` command prints the declared split, case/market identities, and
budgets without constructing an optimizer. The `preflight` command requires
the frozen attempt and cluster native runtime. Do not reuse the attempt path
for changed code or a new statistical design. An interrupted unreceipted cell
stays intact for postmortem; run a new named attempt only after review.
