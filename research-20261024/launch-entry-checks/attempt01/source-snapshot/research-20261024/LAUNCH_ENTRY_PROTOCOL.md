# Bind verified entry receipts to the checked initializer

24 October 2026. One bounded source integration package. The previous initializer
check passed, but it accepted caller-supplied metadata without authenticating the
lock, freeze receipt or current cumulative account. This package connects those
checks to publication of a fresh ledger prefix. It does not run a controller,
freeze a real case or retry the historical v4 attempt.

The preparation input is a completed post-freeze account for the intended
experiment: matching policy, phase metadata_freeze, freeze_passed/metadata_freeze
true, native_dispatch false, complete accounting and absent/reaped owned groups.
Its prior charge must match the lock's carried charge. The current source-check
account supplies this check's cumulative carry; it is not itself a valid account
for preparing numerical entry. No check_passed flag substitutes for a completed
freeze. The function also checks recorded cleanup/next-worker funding against
the already installed global and package limits; this check reserves nothing.

The new preparation function requires an independent caller's expected policy,
lock/receipt/account SHA-256 digests and current cumulative charge. The caller must
already have installed the intended serialized policy context; this function must
not mutate policy, choose an experiment or create launch authority. Resolve the
receipt path to the exact canonical spelling q.run expects. Verify bound bytes,
the account's evidence references and completed accounting/limit fields before
publication. Reuse the actual comparison lock and external-freeze validators,
then derive the canonical accounting record and match the validator's freeze
component before calling the checked initializer. Keep provenance verification
distinct from the truth of receipt assertions and from permission to dispatch.

All invalid metadata must reject before output creation. Existing or partial output
namespaces are never modified, removed, resumed or retried. Publication failures
retain their partial artifacts. No CLI or call to q.run, worker or solver belongs
in this preparation module. Hash checks are point-in-time byte integrity, not a
guarantee against a concurrent external writer; sources and inputs must remain
frozen under the caller's ownership through any later authorized execution.

## One affected source check

- Authoritative carry1524.0216024654942s from
  launch-prefix-checks/accounting.json; ADMIN0. Every old failure and charge stays.
- Additional hard20s; absolute end1544.0216024654942. Work10, outer12.5,
  inclusive15, parent finalization5; one single-thread child and5GiB RSS. The end
  is below both historical1620 and approved1740 dispatch stops. Global
  TOTAL1920/dispatch1740/shutdown180 remain unchanged; no numerical clearance.
- Exclusive launch-entry-checks/attempt01; sole new test file
  test_launch_entry_preparation.py. No rerun of checked arithmetic/initializer
  tests or historical native matrices without a diagnosed source change.
- Handwritten local JSON/byte files and temporary outputs only. Exercise actual
  freeze-receipt validation, canonical builder, initializer and resume readback.
  Full lock/source/environment/fixture verification may be replaced by an explicit
  spy in these tests to avoid research assets; report that coverage limit rather
  than presenting it as an actual qualified lock or controller invocation.
- Cover expected hash/policy/account mismatches, missing evidence roots, incomplete
  accounting, unfunded or wrong totals, canonical receipt paths, invalid external
  freeze receipts and correction funding. Verify no output on input rejection,
  input immutability and refusal to replace an existing namespace.
- Review code/test/wrapper, then freeze exact command, budget and source hashes
  before one invocation. No edits while running, no automatic retry on failure.

Reuse the preceding source-gate monitoring, ownership, cleanup, reaping, artifact
and accounting logic with binding changes only. Charge the maximum observed
elapsed/sampled/reaped CPU plus supervisor CPU, positive whole-process precision
reconciliation, and finalization/preservation. Bound historical evidence may be
byte-hashed without loading research data for analysis. Preserve new immutable
source snapshots and reuse identical prior snapshots by digest. The final account
and all prior failures remain cumulative; no new administration allowance.

A pass establishes only this preparation path on synthetic metadata. It does not
exercise a real native controller, prove transport timing or qualify CF1 charging,
warm starts, feasibility, optimization bounds or model quality. A numerical attempt
still requires a separate prospective decision, fresh source-bound namespace and
applicable resource authority. The stopped v4 namespace and v3 disabling remain.
Keep routine engineering quiet, update the current handoff and back up using
Nathan Cho's requested author/committer identity. No routine Google Doc append.
