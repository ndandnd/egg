# 01 — State of the programme, 2026-08-21 (end of session)

`main` = `de5182f`. Merged since this pack was started: **PR #47** (submit-path
fix, `e1a4e07`), **PR #49** (this documentation pack, `d6aecdf`), **PR #44**
(research inbox, `de5182f`). Nothing else in the table below is merged.

For what every remaining branch is and whether to trust it, see
`06_BRANCH_INVENTORY.md`.

## Settled, with evidence

| Fact | Evidence |
| --- | --- |
| The 60-cell B3 factor pilot population is **complete** | `sacct -j 311153`: all 60 array tasks `COMPLETED`, exit `0:0`. Elapsed 5 s to 1 h 44 m, ~5.1 CPU-hours total |
| It **passes** the hardened audit | 60/60 certified A2 cells, 60/60 converged dictators, 12 cells per setting, Gurobi backend, screen SHA `27c04d82…`, run manifest `9f7529fc…`, run commit `5b63e72…` |
| Its raw tree is pinned **outcome-blind** | `tree_sha256 efc5ca31dcddb21166f6a5da2cf60b4961706c99edf9dbda882f87a18a88ace4`, 363 files, 60 dirs, 17385781 bytes. Captured before the analysis ran, now a frozen constant enforced by analyzer, selector and packager |
| The run commit is genuine | `5b63e72` resolves to a real commit and is an ancestor of `main`; `MANIFEST.json` is one of the 363 anchored files, so tampering with it trips the anchor |
| CI exists | CBC-only GitHub Actions, merged as PR #43 |
| The novelty position holds | No collision found in the 2026-08-20 sweep. Canonical ingestion, dimensional scoring and full-text verification remain pending — do **not** write "re-verified" |
| Those ~90 other cluster jobs are **not** this project | Every `egg` Slurm job name is prefixed `egg-`; `ft_*`, `fx_*`, `b4_*`, `g_*`, `ch_*` match none. No seed-collision risk with 32–47 |

## Deliberately not done

**The preregistered analysis has not been run. No decision is frozen.** Holding
it is what keeps analyzer reviews outcome-blind. It costs nothing: the
confirmation is a ~2–3 hour job whenever it runs.

## Pull requests

| PR | Head | CI | State |
| --- | --- | --- | --- |
| #37 | `36a71be` | check it | B3 closeout: analyzer, selection freeze, pack/import. **Five review rounds.** Last round's only non-same-UID blocker (helper not provenance-pinned) is fixed. Needs a sixth review or a decision to stop |
| #47 | — | — | **MERGED as `e1a4e07`.** Submit-script output-path fix: the array now honours `EGG_RUN_OUT` instead of hardcoding its output path. This is what makes a replication safe -- without it, re-running the pilot wrote into the audited tree |
| #48 | `aab80d5` | **green** | Replication comparator, contract frozen before any replica. Independent review was blocked by an OpenAI safety filter — **still unreviewed** |
| #45 | `5a53c11` | green | B3 confirmation driver. **3 blockers + 3 highs open.** Must not launch |
| #46 | `f709165` | green | ML training-data driver. **Parked**: per-call rather than per-cell wall cap, replay-flag alignment, dual-spread across slots, and it may not encode the price trajectory it claims to learn |
| #44 | — | — | **MERGED as `de5182f`.** Research candidate inbox, now at its canonical home `ref/review_notes/` |
| #41 | `2530ec8` | check | GIRO frozen loader. Clean diff |
| #42 | `18f4c4d` | check | Column proposer lab. Honest negative: 0 of 160 proposals accepted |
| #39 | `2ad05f5` | green | Strict two-cycle witness for B1 |
| #38 | `8521780` | check | Tiny branch-and-price lab. Root intervals matched A2 exactly on seeds 0 and 15 |
| #40 | `80d0ffd` | check | Uplift settlement arithmetic |
| #32 | `8d498b8` | — | B31 boundary corpus. Later/optional |
| #29 | `c32056a` | — | Cloud agent environment. Low priority |

## The blockers that matter, in order

1. **#45 cannot launch anything.** Its launcher can report failure or
   cancellation *after workers were released*, which invites a retry that
   consumes seeds 32–37 twice. Its audit accepts 241 oracle calls against a
   240 budget, a dictator gap of 100.5 against `tol_d = 0.01`, a missing
   dictator record, and a run commit of forty zeroes with no `JOB.json`. Its
   self-test hook accepts any existing file as a permission marker
   (`/etc/hosts` sufficed) and never checks an absolute `EGG_SBATCH`.
2. **#37 needs one more independent review, or an explicit decision to stop.**
   See `05_THREAT_MODEL.md`: every remaining finding requires a local same-UID
   caller, which is not a defensible thing to keep chasing.
3. **#48 is unreviewed.** Its contract is frozen, which is the property that
   matters, but nobody has attacked it. The specific question to ask: *can two
   populations that agree under this comparator yield different preregistered
   decisions?* If yes, the comparator measures the wrong thing.

## Known-unfixed, deliberately

- Same-UID forgeability across the whole pipeline. See `05_THREAT_MODEL.md`.
- A linked-worktree gitfile swap after the provenance precheck (same-UID only).
- `analyze_b2_pilot.py`, `analyze_a6_holdout.py`, `package_a6_holdout.py` and
  `local_a6_preflight.py` still shell a bare `git`. Out of scope for #37; a
  repo-wide follow-up. **Relevant if you run the A6 recovery** — see the
  runbook and note that its recover2 path was never audited for the four
  defect classes found in the B3 code.

## Disaster-recovery status (verified 2026-08-21)

A deliberate "building is on fire" sweep was run. Findings:

- **All project knowledge is on GitHub.** The 34-file continuity pack is on
  `main` (PR #49). Nothing operational lives only on a laptop any more.
- **No unpushed code exists.** Two branches looked orphaned
  (`agent/a6-pilot-selection-closeout`, `agent/a6-holdout-implementation`);
  `git cherry origin/main` proved every commit already equivalent in `main`.
- **Two local-only leftovers were preserved** into
  `local_machine_state/`: one superseded git stash and the untracked
  `.claude/settings.local.json`. See that folder's README.
- **Raw evidence is NOT on GitHub, by design.** `src/runs/` is gitignored and
  lives only on Unicorn. **This is the remaining single point of failure.**

### Which run tree to back up first, and why

Not the B3 pilot. It is re-runnable in about two hours (5.1 CPU-hours, 60
cells, frozen design, burned dev seeds {0,11,15}) and -- because nobody has
seen the outcome yet -- a re-captured anchor would still be genuinely
outcome-blind. Losing it costs cluster time, not the experiment.

**Back up `src/runs/a6_holdout*` first.** Its recovery is gated by two
committed claim files that pin the exact source-tree digest
`2c60b3d2feb1f313cb08541556d5e8f95bf40dc76b2c539d78149dd93ad88749`. Lose that
tree and the recovery can never complete: the claim chain is permanently dead,
there is no third stage, and A6 would need a fresh 128-cell holdout with a new
chain.

A restored backup is **self-verifying**: `canonical_tree_sha256` hashes
path/sha256/size and ignores mtimes, so a tar round-trip preserves it. After
restoring, confirm the pilot tree with

    python3 -c "import sys; sys.path.insert(0,'src')
    from experiments.package_a6_holdout import snapshot_source, canonical_tree_sha256
    s=snapshot_source('src/runs/b3_factor_pilot')
    print(canonical_tree_sha256(s)=='efc5ca31dcddb21166f6a5da2cf60b4961706c99edf9dbda882f87a18a88ace4', s['file_count'])"

Take the tar while no `egg-` array is running (`squeue --me -h -o '%j' | grep
'^egg-'`), or the snapshot is inconsistent.
