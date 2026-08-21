# 02 — What to run when you come back

Everything here is safe to run with no VPN except section 2, which needs the
cluster. If the VPN does not work, sections 1, 3 and 4 still make real progress.

## 0. Orient (2 minutes, no cluster)

```bash
git clone https://github.com/ndandnd/egg.git && cd egg
cat agentic/01_STATE.md
git ls-remote --heads origin | grep -E "b3-pilot-closeout|replication-comparator|b3-submit-out"
gh pr list --state open --limit 15
for n in 37 45 47 48; do printf "#%s " $n; gh pr checks $n | head -1; done
```

If `main` has moved past `ed8b06f`, read the intervening merges before trusting
`01_STATE.md`.

## 1. Did a replication get launched? (no cluster needed to decide what it means)

A 60-cell replication of the pilot into `runs/b3_factor_pilot_replication` may
have been launched at the end of the session. Its purpose: the analyzer
**replays** recorded solver evidence rather than re-solving it, so a replication
is the only empirical check that the pipeline reproduces its own certificates.

**With cluster access:**

```bash
(
    set -uo pipefail
    cd "$HOME/egg/src" || exit 1
    export PATH="/usr/local/slurm/current/bin:$PATH"
    if [ -f runs/b3_factor_pilot_replication/JOB.json ]; then
        J="$(python3 -c 'import json;print(json.load(open("runs/b3_factor_pilot_replication/JOB.json"))["job_id"])')"
        echo "replication job: $J"
        sacct -j "$J" --format=JobID,State,ExitCode,Elapsed -P | grep -vE '\.batch|\.extern'
        ls runs/b3_factor_pilot_replication | wc -l
    else
        echo "no replication was launched"
    fi
)
```

**Then — and this is the important part — verify the ORIGINAL tree is untouched:**

```bash
(
    set -euo pipefail
    cd "$HOME/egg/src"
    python3 - <<'PY'
import json, sys
sys.path.insert(0, ".")
from experiments.package_a6_holdout import snapshot_source, canonical_tree_sha256
snap = snapshot_source("runs/b3_factor_pilot")
got = canonical_tree_sha256(snap)
want = "efc5ca31dcddb21166f6a5da2cf60b4961706c99edf9dbda882f87a18a88ace4"
print("ANCHOR OK" if got == want else f"ANCHOR BROKEN: {got}")
print(f"files={snap['file_count']} dirs={snap['directory_count']} bytes={snap['total_bytes']}")
PY
)
```

Expected: `ANCHOR OK`, `files=363 dirs=60 bytes=17385781`.

**If the anchor is broken, stop.** Something wrote into the audited tree. That is
an engineering incident: preserve everything, write it up in
`doc/ENGINEERING_INCIDENTS.md`, and do not score the population until you
understand what changed. The most likely cause would be a pilot re-run launched from a checkout
*predating* `e1a4e07` (PR #47), since the un-fixed submit script hardcoded its
output path and ignored `EGG_RUN_OUT`. Confirm the launching checkout contained
that commit.

### What the replication result means

Do **not** eyeball the two runs and form an impression. The comparison rule is
frozen in PR #48 (`doc/B3_REPLICATION_COMPARATOR_SPEC.md`) precisely so it
cannot be rationalized after the fact: all 60 cells matched by identity,
agreement is **60/60**, compared fields are `lb_best`, `ub_ch`, both raw uplift
endpoints, the dictator bounds and `certified`, tolerance operand-scaled with a
floor of 1e-2. Run the committed comparator, not a judgement call.

- **60/60 agreement** → the replay-based certificate is empirically reproducible.
  Record it; it materially strengthens the flagship and answers the sharpest
  criticism of the whole approach.
- **Any disagreement** → an engineering incident to investigate, **never** a
  choice of which run to score. The original run stays canonical either way.
- Run manifests and `run_commit` are *expected* to differ between the two runs.
  That is not a disagreement; provenance fields are excluded by the contract.

Caveat to record honestly: PR #48 was never independently reviewed (the review
attempt was blocked by a safety filter). Before leaning on its verdict, get
someone to answer one question: *can two populations that agree under this
comparator produce different preregistered decisions?* If they can, the
comparator is measuring the wrong thing.

## 2. The A6 recovery — only if you have cluster access and full attention

`agentic/A6_RECOVER2_OPERATOR_RUNBOOK_20260821.md` has an eight-check read-only
preflight and the single exact command. Read all of section 0 of that file first.
It is **one-shot**: an `O_EXCL` claim file is created before any outcome
validation, everything before that point is retryable, everything after is
permanent, and there is no third stage.

**Added caution since it was written:** four defect classes were found in the
sibling B3 code (duplicate-JSON-key acceptance, provenance answerable through
`PATH`/`GIT_DIR`/`DEVELOPER_DIR`, validate-then-copy divergence, guards that
trust the environment). The A6 packager was **never audited** for them. If you
can spare an agent before consuming the one shot, have it audit
`package_a6_holdout.py` for those four classes — the brief is `JOB 4` in
`task_briefs/CURSOR_TASKS_ROUND3_20260821.md`. The claim files gate the one shot,
so duplicate-key parsing there is the one that would hurt most.

Value: the raw run from job `248911` already exists. Closing this converts
existing compute into a scoreable A6 adoption-gate result at zero cluster cost.
The gate is `MIN_A6_CERTIFIED = 61`, `RATIO_BAR = 0.85`, `WIN_BAR = 38`, in
`analyze_a6_holdout.py`, and it is only reachable after a successful import.

## 3. The critical path to the flagship decision (no cluster needed until the end)

In order. Do not skip a step to save time; each one exists because a review
found a real defect at that step.

1. **Merge PR #47** (submit-path fix). Green and clean. Nothing that re-runs the
   pilot is safe without it.
2. **Get PR #37 to a decision.** Either one more independent review by an agent
   that did not write it, or an explicit choice to stop hardening and merge on
   the bounded claim in `05_THREAT_MODEL.md`. Five rounds have happened; every
   remaining finding needs a local same-UID caller.
3. **Merge #37.** Then, on the cluster, with no `egg` array running:
   `git pull --ff-only`.
4. **Re-run the audit read-only, with the newly merged code:**
   ```bash
   ( set -euo pipefail; cd "$HOME/egg/src"
     source cluster/unicorn_env.sh
     python experiments/audit_b3_factor_pilot.py --runs runs/b3_factor_pilot )
   ```
   **Never pass `--out` into the raw tree again.** `AUDIT.md` is already one of
   the 363 anchored files; rewriting it can change the tree digest and break the
   anchor. The recorded PASS came from the pre-#37 audit implementation, so this
   re-run matters.
5. **Verify the anchor immediately before and immediately after** the analysis
   (the snippet in section 1). Record both values in the decision log. The
   analyzer now freezes and digest-authenticates internally, but an independent
   operator-side observation is cheap and is what you will cite later.
6. **Run the analysis, then read `boundary_adjacent` before anything else.** If
   it is `true`, the median sits within 1e-9 of the 0.04 threshold: stop and get
   a human decision. The confirmation driver refuses to launch on it by design.
7. **Freeze the selection artifact and commit** the analysis, `DECISION.json`,
   `doc/DECISION_LOG.md` and `doc/RESEARCH_STATUS.md`, code-first then
   artifact-second, regenerating byte-identically to prove determinism.
8. **Only a committed GO authorizes the confirmation** — and only with a
   repaired, independently re-reviewed PR #45. `NO-GO` and `UNDER-RESOLVED`
   produce no selection artifact and end the factor line as preregistered.
   That is a result, not a failure.

## 4. Work that needs no cluster and no VPN

- Repair PR #45's three blockers (`JOB 2` in
  `task_briefs/CURSOR_TASKS_ROUND2_20260821.md`, plus the newer findings in
  `01_STATE.md`).
- Get PR #48 independently reviewed (`JOB 3` in
  `task_briefs/CURSOR_TASKS_ROUND3_20260821.md`).
- The cite-and-scope pass: fold `DEEP_RESEARCH_20260820.md`'s candidates into
  `ref/papers.csv` and the novelty matrix, and correct the B2 stabilization
  claim to "*dense iterative* stabilization loses end-to-end *at small n*".
- The OMIE market-calibration spike (see `03_RESEARCH.md`). Free data, no
  cluster, and it converts the synthetic market from assumed to calibrated.
- Write the B1 chapter around the machine-checked two-cycle witness in PR #39.
