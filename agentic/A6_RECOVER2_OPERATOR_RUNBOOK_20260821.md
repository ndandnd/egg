# A6 second-stage recovery (EI-027) — operator runbook

Date: 2026-08-21. Written from `origin/main` (`ed8b06f`) by reading the merged
code, not from memory. **Read all of section 0 before typing anything.**

This is the first operator documentation for `recover2-pack`.
`doc/UNICORN_RUNBOOK.md` ends with the EI-026 `recover-pack` section and has
**no EI-027 section**, and `doc/ENGINEERING_INCIDENTS.md:1354-1358` is stale —
it says the machinery is "implemented on an unmerged branch" and "no operator
command is published until then", but it merged in commit `7bccddf`, which is
an ancestor of current `main`. Fold this file into `doc/UNICORN_RUNBOOK.md` and
fix that stale paragraph once the recovery is done.

## 0. The three things that will hurt you

1. **There is no dry-run, preflight, `--check`, or `--verify` mode.** None of
   the four subcommands (`pack`, `import`, `recover-pack`, `recover2-pack`) has
   one. The preflight in section 2 is therefore *manual shell assertions* —
   the code cannot rehearse itself.

2. **The one-shot point is precise, and everything after it is permanent.**
   The attempt is burned by an `O_EXCL` create of
   `src/runs/a6_holdout.RECOVERY2_CLAIM.json` inside `claim_recovery2`. Every
   gate before that (there are eighteen) leaves the claim unconsumed and is
   freely retryable. Every failure *after* it is permanent:

   ```text
   A6 second-stage recovery was already claimed; no third
   recovery stage exists: .../a6_holdout.RECOVERY2_CLAIM.json
   ```

   There is no third stage and no bypass flag. A post-claim failure is an
   incident to record in `doc/ENGINEERING_INCIDENTS.md`, not something to
   retry.

3. **`squeue` must be on `PATH`, and this is what broke EI-026.** Slurm
   quiescence is checked three times (once before the claim, twice after). The
   check refuses outright if `squeue` is missing — "squeue is unavailable;
   package on Unicorn after the job ends". The original EI-026 failure was a
   non-login shell without `squeue` on `PATH`. Export it explicitly.

Two more facts worth knowing before you start:

- **Do not override `--selection`.** The frozen canonical path is enforced;
  any other value is refused.
- **`--failure-fingerprint` is free-form** and validated only for
  non-emptiness, but it is frozen permanently into the claim, the bundle
  manifest, and the transfer receipt. Choose it deliberately; a suggested
  value is in section 3.

## 1. What this does and does not decide

Packaging is **decision-blind by design**. `recover2-pack` sets
`expect_cg_certified_method=None` and records `"decision_computed": false`, so
it cannot pass or fail on the A6 adoption gate. The gate lives in
`src/experiments/analyze_a6_holdout.py` (`MIN_A6_CERTIFIED = 61`,
`RATIO_BAR = 0.85`, `WIN_BAR = 38`) and is only reached by the analyzer after a
successful import on the Mac. So this command tells you nothing about whether
A6 wins; it only moves the evidence.

## 2. Read-only preflight — run this first, change nothing

Every line is read-only. Run it as one block; a subshell keeps a failure from
closing your login session. If any line prints `FAIL`, stop and diagnose;
do not proceed to section 3.

```bash
(
    set -uo pipefail
    cd "$HOME/egg/src" || exit 1
    export PATH="/usr/local/slurm/current/bin:$PATH"

    ok() { printf '  OK   %s\n' "$1"; }
    bad() { printf '  FAIL %s\n' "$1"; }

    echo "== 1. Slurm tooling (this is what broke EI-026) =="
    command -v squeue >/dev/null && ok "squeue on PATH: $(command -v squeue)" \
        || bad "squeue NOT on PATH — the recovery will refuse"

    echo "== 2. the one-shot claim must NOT already exist =="
    if [ -e runs/a6_holdout.RECOVERY2_CLAIM.json ]; then
        bad "RECOVERY2 claim already exists — the one shot is spent, STOP"
    else
        ok "no RECOVERY2 claim present"
    fi

    echo "== 3. the two prior claims must exist with EXACT digests =="
    for pair in \
      "runs/a6_holdout.CLOSEOUT_CLAIM.json 1b0acf0b8232d4b08e764564e2732fcfa9c28dd53456a1415085b77cb38f6675" \
      "runs/a6_holdout.RECOVERY_CLAIM.json 88c22f06ce6bc8dcff56c0d6737c91bbd39fe8da79c2b6ba6d2a987b6b6abe88"
    do
        set -- $pair
        if [ ! -f "$1" ]; then bad "missing $1"; continue; fi
        got="$(sha256sum "$1" | cut -d' ' -f1)"
        [ "$got" = "$2" ] && ok "$1 digest matches" \
            || bad "$1 digest is $got, expected $2"
    done

    echo "== 4. clean tracked tree, HEAD, and the three required ancestors =="
    if [ -n "$(git -C .. status --porcelain --untracked-files=no)" ]; then
        bad "tracked tree is dirty — commit or stash first"
    else
        ok "tracked tree clean"
    fi
    HEAD_SHA="$(git -C .. rev-parse HEAD)"; ok "HEAD = ${HEAD_SHA}"
    for c in 740ab0c1578b454268102c0bb15b1104d9ac8d9d \
             b81b15ace8ffd7301ce93f349fdb643cdefd5da6 \
             74a9c5d56ae328b5c394537007cc7cefdb6e3441
    do
        git -C .. merge-base --is-ancestor "$c" HEAD \
            && ok "ancestor present: ${c:0:12}" \
            || bad "NOT an ancestor of HEAD: ${c:0:12}"
    done

    echo "== 5. the live raw tree must still match the original claim =="
    python3 - <<'PY'
import json, sys
sys.path.insert(0, ".")
from experiments.package_a6_holdout import snapshot_source, canonical_tree_sha256
claim = json.load(open("runs/a6_holdout.CLOSEOUT_CLAIM.json"))
src = claim["document"]["source"]
snap = snapshot_source("runs/a6_holdout")
live = {"canonical_tree_sha256": canonical_tree_sha256(snap),
        "file_count": snap["file_count"],
        "directory_count": snap["directory_count"],
        "total_bytes": snap["total_bytes"]}
bad = [k for k in live if src.get(k) != live[k]]
print("  OK   live raw tree matches the original claim" if not bad
      else f"  FAIL live raw tree drifted on {bad}: {live}")
print(f"       launch_job_id = {claim['document']['launch_job_id']}")
print(f"       preflight_sha256[:12] = {claim['document']['preflight_sha256'][:12]}")
PY

    echo "== 6. Slurm quiescence for the launch job =="
    JOB="$(python3 -c 'import json;print(json.load(open("runs/a6_holdout.CLOSEOUT_CLAIM.json"))["document"]["launch_job_id"])')"
    rows="$(squeue --noheader --me --format='%F' | grep -c "^${JOB}$" || true)"
    [ "$rows" = "0" ] && ok "job ${JOB} is quiescent" \
        || bad "job ${JOB} still has ${rows} row(s) in the queue"

    echo "== 7. no existing package with this prefix =="
    PREFIX="$(python3 -c 'import json;d=json.load(open("runs/a6_holdout.CLOSEOUT_CLAIM.json"))["document"];print(f"a6_holdout-job{d[\"launch_job_id\"]}-{d[\"preflight_sha256\"][:12]}-")')"
    if ls runs/a6_holdout_packages 2>/dev/null | grep -q "^${PREFIX}"; then
        bad "a package already exists with prefix ${PREFIX} — this blocks forever"
    else
        ok "no package with prefix ${PREFIX}"
    fi

    echo "== 8. the frozen selection artifact must be untouched =="
    SEL="../result/a6_pilot/20260819T005514Z/SELECTION.json"
    got="$(sha256sum "$SEL" | cut -d' ' -f1)"
    [ "$got" = "026ddc38e90f9dd2e9342a50cfb5550bc52731c5f1ee67d87d53008bd6b4b507" ] \
        && ok "SELECTION.json digest matches" || bad "SELECTION.json digest is $got"
)
```

## 3. The one command — only if every line above printed OK

This burns the single remaining attempt. Do not run it unattended, and do not
run it if you are about to lose your connection: a post-claim failure is
permanent.

Pick the fingerprint deliberately. The natural value comes from the EI-027
evidence block in `doc/ENGINEERING_INCIDENTS.md`: the physical-bridge
validation abort on cell `a2 seed=22 n=12 b=0.01` at iteration 24, where the
reconstruction adjustment `1.0761229077616008e-05` exceeded the operand-scaled
tolerance `2.4175838553896413e-07`. The string below records that; it is
free-form but permanent.

```bash
(
    set -euo pipefail
    cd "$HOME/egg/src"
    export PATH="/usr/local/slurm/current/bin:$PATH"
    export EGGLAB_REQUIRE_GRB=1
    source cluster/unicorn_env.sh

    python experiments/package_a6_holdout.py recover2-pack \
        --root runs/a6_holdout \
        --out runs/a6_holdout_packages \
        --recovery2-code-commit "$(git -C .. rev-parse HEAD)" \
        --incident-id EI-027 \
        --original-claim-sha256 \
          1b0acf0b8232d4b08e764564e2732fcfa9c28dd53456a1415085b77cb38f6675 \
        --first-recovery-claim-sha256 \
          88c22f06ce6bc8dcff56c0d6737c91bbd39fe8da79c2b6ba6d2a987b6b6abe88 \
        --failure-fingerprint \
          "ei027-physical-bridge-validation-abort-a2-s22-n12-b0.01-it24-adj1.0761229077616008e-05-tau2.4175838553896413e-07"
)
```

`--root`, `--out`, and `--selection` are all at their defaults and may be
omitted; `--selection` must never be overridden.

On success it prints `bundle_dir`, `archive`, `sidecar`, `manifest`,
`audit_summary`, and `archive_sha256`. Record all six.

## 4. If it fails

**Before the claim was created** (any of the eighteen pre-claim gates): nothing
was written, `runs/a6_holdout.RECOVERY2_CLAIM.json` does not exist, and you may
fix the cause and retry. Confirm with
`test ! -e runs/a6_holdout.RECOVERY2_CLAIM.json`.

**After the claim was created**: the attempt is spent. Do not retry, do not
design a third stage, do not delete the claim. Capture, in this order:

1. the full stderr of the failed command;
2. `ls -la runs/a6_holdout.RECOVERY2_CLAIM.json` and its sha256;
3. `ls -la runs/a6_holdout_packages/` — a leftover
   `.<bundle>.staging-*` directory means staging rollback also failed and is
   preserved deliberately for review;
4. whether the destination bundle directory exists and contains
   `.publication-incomplete` (a post-rename failure preserves it; that
   directory will also block gates A18/C9 permanently);
5. `sha256sum runs/a6_holdout.CLOSEOUT_CLAIM.json runs/a6_holdout.RECOVERY_CLAIM.json`
   — these must be byte-identical to section 2 and are never modified by a
   successful run.

Then write a new incident entry. The A6 line ends unscored rather than being
recovered a third time.

## 5. After success

The bundle is transferred to the Mac and imported with the `import`
subcommand, which requires local `HEAD` to equal the
`--recovery2-code-commit` you used and re-proves all three ancestries. Only
then does `analyze_a6_holdout.py` compute the adoption gate, and it requires
`analysis_code_commit` to equal the recovery2 commit plus the chronology
`closeout <= recovery1 <= recovery2 <= import`. Plan to import from the same
commit you package from.
