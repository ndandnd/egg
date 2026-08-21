# 06 — Branch inventory: what every remote branch is, and whether to trust it

Written 2026-08-21 during a disaster-recovery sweep. `main` = `de5182f`.

A fresh clone sees ~20 remote branches with cryptic names. This tells you which
matter, which are historical, and which must not be merged. **Verify heads
before acting** -- `git ls-remote --heads origin`.

## Live work — read these first

| Branch | Head | What it is | Merge? |
| --- | --- | --- | --- |
| `cursor/b3-pilot-closeout-5fa0` | `36a71be` | **The flagship analyzer** (PR #37): scores the B3 pilot, freezes the confirmation selection, packs the transfer bundle. Five independent review rounds; the last non-same-UID blocker is fixed; now integrated with PR #47's job-binding contract | **Not yet.** Needs a sixth review or an explicit decision to stop hardening (see `05_THREAT_MODEL.md`) |
| `cursor/b3-confirmation-driver-eea3` | `5a53c11` | PR #45: launches the fresh-seed confirmation on seeds 32-37 | **NO.** 3 blockers: launcher can report cancellation *after* releasing workers (invites a retry that spends the one-shot seeds twice); audit accepts 241/240 oracle calls and a 100.5 dictator gap against `tol_d=0.01`; self-test hook accepts any existing file as its permission marker |
| `cursor/replication-comparator` | `aab80d5` | PR #48: the frozen 60/60 comparison rule for a pilot replication | Only after review. Contract is frozen (good) but nobody has attacked it. Ask: *can two populations that agree under this comparator yield different preregistered decisions?* |
| `cursor/ml-data-driver-eea3` | `f709165` | PR #46: ML training-data emission | **Parked.** Per-call rather than per-cell wall cap; replay-flag alignment; dual-spread across slots; may not encode the price trajectory it claims to learn |

## Laboratory PRs — real work, unreviewed, none urgent

| Branch | Head | What it is |
| --- | --- | --- |
| `cursor/tiny-branch-price-lab-352b` | `8521780` | PR #38: branch-and-price exactness lab. Its root intervals matched A2's certified intervals *exactly* on seeds 0 and 15 -- early evidence the B&P root really computes `z_CH` |
| `cursor/strict-cycle-minimizer-4a64` | `2ad05f5` | PR #39: machine-checked strict two-cycle witness for B1, with load-uniqueness margins. **Use this for the B1 chapter; do not redo it** |
| `cursor/uplift-settlement-1d7b` | `80d0ffd` | PR #40: convex-hull settlement / lost-opportunity-cost arithmetic. A regret extension was requested and never done |
| `cursor/frozen-loader-9213` | `2530ec8` | PR #41: manifest-verified GIRO freeze/load path. Cleanest diff of the round |
| `cursor/local-column-proposer-6ec0` | `18f4c4d` | PR #42: local-move column proposer. **Honest negative: 0 of 160 proposals accepted** under exact reduced-cost plus replay admission |
| `cursor/b31-boundary-corpus-5fa0` | `8d498b8` | PR #32: B31 switch-boundary corpus builder. Later/optional; already merged with main once |
| `cursor/setup-cloud-agent-environment-eea3` | `c32056a` | PR #29: cloud-agent environment. Low priority |
| `cursor/b3-submit-out-fix` | `770cb60` | **MERGED** as `e1a4e07`. Left for reference |
| `cursor/github-ci-cbc-eea3` | `dfbbb9f` | **MERGED** as PR #43: the CBC-only CI gate |
| `agentic/continuity-20260821` | `37a8624` | **MERGED** as PR #49: this documentation pack |

## Historical — merged or superseded, safe to ignore

`agent/a6-closeout-package-integration`, `agent/a6-closeout-provenance`,
`agent/a6-load-reconstruction-fix`, `cursor/a6-ei026-recovery-5fa0`,
`cursor/ei027-recovery-5fa0`, `cursor/a6-local-preflight-5fa0`,
`cursor/b3-factor-pilot-launcher-eea3`, `cursor/b3-factor-pilot-spec-5fa0`,
`cursor/b3-factor-screen-5fa0`, `cursor/b3-uplift-baseline-5fa0`.

These are the A6 recovery chain and the B3 pilot's own spec/screen/launcher
work, all already in `main`. They are kept because the A6 claim chain pins
specific commits (`740ab0c`, `b81b15a`, `74a9c5d`) that the one-shot recovery
verifies as ancestors -- **do not delete them**.

## The integration trap that already bit once

PR #47 merged while PR #37 was in review and changed the job-binding contract:
`bind_job_id` gained a mandatory launch token, `JOB_SCHEMA` moved to
`b3-factor-pilot-job-v2`, and the binding now writes a `JOB.sha256` file. Four
**hardcoded** `"b3-factor-pilot-job-v1"` literals in the analyzer, selector and
packager silently rejected the new binding. Local test runs passed; only CI --
which tests the PR merged with its base -- caught it.

Two lessons: reference the constant, never the literal; and when several
long-lived branches touch the same contract, **trust CI on the merge commit
over any local run**. A consequence to expect: a run tree bound under #47
carries `JOB.sha256`, so its file count is one higher than the canonical pilot
tree's 363. The frozen anchor describes the original tree and is unaffected.
