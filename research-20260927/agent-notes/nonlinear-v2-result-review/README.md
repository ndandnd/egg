# Nonlinear v2 result review package

This package contains an independent, conditional numerical reconstruction of the sealed v2 pilot and a separate strict protocol verdict. The numerical evidence audit passes; the frozen cumulative hull-polishing time cap does not. The pilot is therefore not an admitted on-protocol result. Solver global bounds remain conditional on the recorded GRB bounds; no exact full-fleet optimum is claimed.

`audit_nonlinear_v2.py` and the `independent_*.py` helpers use Python's standard library, reconstruct checks from the sealed records, and inspect pinned Git blobs. They do not import the project implementation or call an optimizer. Raw solver and wrapper logs are validated by hash and are not printed or copied into the report.

From the workspace root, reproduce the strict full-archive audit with:

```sh
python3 journal-research-work/research-20260927/agent-notes/nonlinear-v2-result-review/audit_nonlinear_v2.py \
  --repository "$PWD/journal-research-work" \
  --attempt "$PWD/journal-research-work/result/sistig_nonlinear/20260927-attempt2" \
  --manifest-sha256 68032692ea5c5b349115bd6bd64740f0bd799fac9a8a4dcdf09462a844901cf9 \
  --out "$PWD/journal-research-work/research-20260927/agent-notes/nonlinear-v2-result-review/audit-report-full.json"
```

The full archive is required for strict verification. The public-copy check uses only the exact pinned publication omissions and keeps full mode strict:

```sh
python3 journal-research-work/research-20260927/agent-notes/nonlinear-v2-result-review/test_public_copy_mode.py
```

That test builds a temporary same-layout public subset from the sealed raw attempt, performs the complete public-mode audit, confirms full mode rejects the subset, and confirms public mode rejects a missing scientific file. It removes its temporary copy afterward. `audit-report-full.json` and `audit-report-public.json` record both completed reconstructions. `REVIEW.md` describes the evidence, exact timing exception, and scope.
