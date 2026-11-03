# New-output accounting prefix

`src/experiments/launch_prefix_initializer.py` adds
`initialize_new_output(output, *, accounting, binding, reconciliation)` without a
CLI or launch path. It accepts exactly the existing recovery campaign binding
keys, validates supplied absolute references and lowercase SHA-256 metadata,
rebuilds the accounting record with the checked pure builder, and requires exact
`canonical_base_s + external_correction_s == reconciled_total_s` before creating
the output directory. No tolerance or clamp hides floating-point charge loss.

The exclusive directory creation is followed by the existing runner's exclusive
campaign writer and hash-linked ledger appender: canonical carry/freeze, then a
`supervisor_cpu` correction with reason
`external_freeze_reconciliation_and_closure` and the supplied accounting reference
and hash. The real `recovery_qualification.resume_state` consumer checks the new
prefix with canonical budget components and no tasks. Only zero completed tasks
and an exactly reconciled total permit the flat `initialization.json` receipt.
That receipt is informational and explicitly grants no launch permission or
timing proof. Input metadata are copied; references are not read or represented
as independently verified provenance. No assets or models are read.

Failures after directory creation intentionally preserve every published artifact;
an existing or partial namespace blocks another initialization. There is no
cleanup, rewrite, automatic retry, or launch. Existing frozen sources are untouched.

The new handwritten-metadata tests cover actual cancellation values through JSON
and the real resume consumer, rejection of the old raw-freeze prefix, zero and
positive corrections, immutable inputs, malformed metadata and forged records,
an exact one-ULP folded-charge loss, existing-output preservation, and an injected
receipt-publication failure that leaves a partial output and blocks retry. These
sources were prepared without imports, test execution, native work, or data reads;
the parent may perform the separately bounded new-source gate.
