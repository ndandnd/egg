# Launch-entry source review

24 October 2026. Independent source-only review of the new preparation adapter,
its handwritten temporary-metadata tests, implementation/protocol/wrapper notes,
and the driver diff from the reviewed launch-prefix gate. The checked initializer,
canonical accounting builder, actual comparison lock/freezer validators and
recovery run/resume entry were read for the interface review. No project imports,
tests, native work, research-input parsing, historical retry or commits were
performed for this review.

No source blocker was found in the reviewed scope. The adapter requires explicit
independently supplied lock, receipt and account SHA-256 roots, expected policy
and cumulative total. It authenticates each root's bytes before parsing the
object, canonicalizes references as q.run does, and requires the caller's
matching q/adapter policy, validator/freezer bindings and timing constants to be
installed already. It installs no context and has no controller, CLI, worker or
solver invocation.

The input account must describe a completed metadata_freeze for the experiment,
with a passed freeze, complete accounting and absent/reaped owned groups. Its
prior charge must equal the lock's carry; current and prior charges must add
exactly to the independently expected total. A source-check account is rejected.
The evidence map must contain the rooted lock and receipt and use canonical
absolute paths; every evidence digest is checked. Recorded global limits must
match the installed limits, and the reconciled total must retain the actual
next-worker, shutdown, supervision and final-analysis funding. These checks
reserve no resources.

The adapter calls the actual comparison verify_lock and freeze_accounting, then
passes the receipt's raw and cumulative charges to the checked canonical builder.
It requires the freezer's returned lock to equal the canonical subtraction-based
freeze result. Root bytes, evidence and installed bindings are checked again
before publication. The existing initializer supplies the exact final fold
check, exclusive creation, two-event prefix and real resume-consumer readback;
an existing or partial namespace, including an output symlink, is refused.
Publication failures retain the partial output and block reuse.

The sole new test file mocks the complete lock verifier to avoid qualifying or
reading real fixture/environment assets. This is an explicit coverage limit:
the gate cannot establish a real source/environment/fixture lock or controller
invocation. Tests exercise the real freeze validator, builder, initializer and
resume consumer using temporary handwritten files. They cover changed or missing
roots, missing or changed evidence, policy/phase/completion/limit mismatches,
wrong or unfunded totals, negative correction, invalid external-freeze receipt,
canonical path aliases, zero/positive correction, input-byte and argument
immutability, and existing-output preservation. The decimal-charge example
checks that cumulative-minus-carry differs from raw charge and still resumes
exactly; the checked initializer retains its previously reviewed inexact-fold
rejection.

The new driver differs from the reviewed prefix driver only in scope, namespace,
carry/predecessor bindings, source inventory, selected test and corresponding
wording. Monitoring, ownership, cleanup, output audit and accounting bodies are
preserved. Carry1524.0216024654942, ADMIN0, hard20 ending1544.0216024654942,
work10/outer12.5/inclusive15/closure5, one thread and5GiB match the protocol. Only
the new entry test is selected. Prospective command/budget/source bindings remain
the parent's final check before the sole authorized source invocation.

Hash verification authenticates point-in-time bytes, not the truth of receipt
assertions, exclusive context ownership or immunity to a concurrent writer.
The caller must retain frozen inputs and serialization through any later
separately authorized execution. A passing synthetic gate grants no native
clearance, timing proof, experiment permission or authority to reuse the stopped
v4 namespace.
