# Controller entry preparation implementation

`experiments.launch_entry_preparation.prepare_new_output` accepts lock, freeze
receipt and current postfreeze accounting paths, three independently supplied
SHA-256 roots, the independently reconciled cumulative charge, and the expected
experiment policy. It resolves input references as `q.run` serializes them and
prepares only a new output namespace. It never invokes `q.run`, a CLI, a solver,
or an adapter context; the caller must already own serialization and install the
matching q/adapter policy, verifier/freezer and timing constants.

The account must have experiment policy, `phase=metadata_freeze`,
`freeze_passed=true`, `metadata_freeze=true`, `native_dispatch=false`, complete
accounting observations and absent/reaped owned groups, no unresolved accounting
or lower-bound charge, and carried/current charges that reconcile exactly to the
independently expected total. Its limits must equal the installed controller
limits and retain next-worker dispatch, shutdown, supervision and final-analysis
funding. Its evidence map must bind the checked lock and receipt and every
canonical absolute evidence reference is hash verified. A source-check account
such as the current `launch-prefix-checks/accounting.json` is carry for a future
source gate, not an admissible postfreeze entry account.

The function calls the actual comparison adapter `verify_lock` and
`freeze_accounting`, builds canonical accounting from the checked receipt's raw
and cumulative charges plus the reconciled current total, and requires the
consumer's freeze result to equal the canonical result. Immediately before the
checked initializer is called, roots, accounting evidence and installed policy
are checked again. The initializer retains its exact resume-consumer readback.
An existing directory, partial output or symlink is rejected; any publication
failure remains on disk and blocks reuse.

These checks are snapshots and cannot provide an atomic filesystem guarantee or
prove exclusive ownership of the caller's installed context. The result does
not reserve funding, provide timing proof or grant launch permission. Callers
must independently source the expected hashes; self-described hashes are not
authority. No historical stopped campaign or sealed/data/model/cluster input
was read or edited for this implementation.

The new tests use handwritten temporary metadata. Only the full lock verifier
is mocked to avoid fixture/environment qualification. Actual adapter freeze
receipt validation, canonical accounting, initializer publication and recovery
resume readback are exercised. Cases cover rooted-byte changes, missing roots
and closure references, policy/phase/limit/completion mismatches, wrong totals,
unfunded or negative corrections, zero/positive corrections, invalid real freeze
receipts, canonical path references, closure mutation during verification and
retention of a partial namespace. Success also checks input bytes and caller
arguments are unchanged; a decimal-charge case checks floating subtraction
through the actual freezer and initializer. This is intentionally not full lock,
fixture/environment, native mechanism or controller execution coverage.

The implementation author did not run tests, import project modules, commit, or
execute native work. The parent will perform the one externally supervised
metadata check after independent review.
