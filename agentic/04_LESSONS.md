# 04 — Lessons from this campaign

Read before writing code or dispatching agents. Every item below was paid for.

## About review

1. **Author repairs, non-author reviews.** Every real defect this campaign was
   found by someone who did not write the code. Five review rounds on one PR
   each found something, twice in a fix its author was confident in. Never let
   a PR's author be its reviewer.
2. **A self-report describes intent, not coverage.** Agents reported
   "comprehensive gate", "all findings closed", "zero bare-git remaining" --
   and independent reviewers then re-exploited them. The assistant writing this
   made the same class of false completeness claim three times.
3. **Fix the class, not the instance.** Round 2 digest-checked checkpoints;
   round 3 found the sidecars; round 5 found the packager. Each round patched
   where the reviewer pointed instead of sweeping for the pattern. When a
   review finds a defect, grep for every other place the same shape occurs
   *before* replying.
4. **Ask reviewers to falsify named claims, not to "review".** The requests
   that found real defects listed explicit claims (A-E) and said "assume a gap
   exists; do not accept the author's framing". Templates in
   `review_requests/`.
5. **A green test suite is not a green PR.** CI failed at `git diff --check` on
   a trailing blank line, so pytest never ran, and the previously reported
   green was from an older head. Check the CI *conclusion* on the *exact head*.
6. **Regressions can pass vacuously.** A laundering test passed only because
   its fixture lacked `JOB.json`, so the code path it claimed to cover never
   ran. When a test passes first try, verify it fails against the unfixed code.

## About integrity engineering

7. **Verify at the point of consumption, not by re-reading a path.** A
   post-scoring re-hash cannot detect substitute-then-restore. Hash the same
   buffer you parse (`expected_sha256` on the read helper). This took three
   rounds to learn.
8. **Environment cannot be identity.** `SLURM_ARRAY_JOB_ID` is
   caller-controlled. So is `PATH`, `GIT_DIR`, and on macOS `DEVELOPER_DIR`
   (because `/usr/bin/git` is an `xcrun` dispatcher). Build environments from
   an **allowlist**, never a denylist.
9. **A recorded boolean is not a control.** `run_commit_verified` was recorded,
   then enforced, then still laundered by editing it. The fix is for the
   consumer to re-verify independently; the flag is diagnostic.
10. **Pin every file that executes.** A new shared helper was created and
    omitted from every provenance allowlist, so a commit changing only it was
    accepted against an older reviewed commit -- false attribution from
    ordinary maintenance, no attacker needed.
11. **Use the primitive the repo already has.** A duplicate-JSON-key
    vulnerability (`"state": "NO-GO"` then `"state": "GO"`, last key wins) was
    introduced by new code using plain `json.loads` while
    `b3_pilot_evidence.strict_json_loads` already refused duplicates.
12. **Know when to stop.** Every remaining finding requires a local same-UID
    caller. That game does not terminate. Bound the claim instead --
    `05_THREAT_MODEL.md`.

## About the cluster

13. **Never modify a checkout that running jobs read from.** Array tasks
    execute from `$HOME/egg/src`; merging or pulling mid-array makes later
    tasks run different code than earlier ones. Per-cell `run_commit` binding
    would catch it, but the run is wasted.
14. **An empty `squeue` is not a completed population.** Use `sacct` and
    require every task `COMPLETED` with exit `0:0`, then the audit.
15. **A socket timeout is a reply timeout, not a submission failure.** Verify
    by counting queued jobs, never by exit code.
16. **Check what the submit script actually does.** The launcher honoured
    `EGG_RUN_OUT` for its guards while the `.sub` hardcoded `--out`, so a
    "replication" would have passed every guard and then written into the
    audited tree.
17. **Wrap cluster blocks in a subshell** `( ... )`. A top-level `set -e` once
    disconnected the operator's SSH session.
18. **Never re-run the audit with `--out` into the raw tree.** `AUDIT.md` is
    one of the 363 anchored files; rewriting it can break the anchor.

## About agents

19. **`gh api user` returns 403 for Cursor agents** -- they authenticate as a
    GitHub App integration token, which GitHub forbids from calling `/user`.
    This is not an authorization failure and no `GH_TOKEN` is needed; commit
    authorship comes from `git config`. Working gate: remote-URL check plus
    `git push --dry-run`.
20. **Never assume a branch name.** Cursor appends suffixes (`-eea3`, `-5fa0`).
    `git ls-remote --heads origin` first.
21. **One self-contained paste block per agent.** No cross-references to files
    the agent cannot see; include the gate, the scope and the report format.
22. **Adversarial security prompts can trip provider safety filters.** One
    review was refused as "potential high-risk cybersecurity activity". Frame
    reviews as integrity/correctness verification of one's own research code.
23. **Protocol boundaries need stating explicitly.** An agent wrote unreviewed
    first-run output into `result/` and edited `doc/DECISION_LOG.md` because
    the brief did not forbid it in those words.
