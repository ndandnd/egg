# Parent direction: preserve current phase carry without changing qualified code

Review PRIMITIVE_TO_FREEZE_ACCOUNTING.md. Prefer its narrow research-driver
contract if and only if the real component primitive genuinely passes with closed
ownership and a completed current account P. This is direction, not a metadata
command manifest or execution clearance; the primitive has not run.

Do not call the unchanged core.freeze CLI with a stale source account to omit
primitive spend. Do not modify/alias/overwrite source01. A new source-bound
research driver may enter the existing revision6 context and invoke the existing
adapter.freeze API with P, reproducing exact lock/design/check paths and adding
the completed-primitive/source-proof/current-budget guards from that note. This
is an explicit phase-binding adaptation with stricter current inputs; it neither
changes production guards nor retroactively claims source01 tested the new
driver. Parent must review and bind its exact bytes/arguments before execution.

Require current source bytes and passed source01 receipts, completed linked P,
actual primitive command/result/ownership/accounting hashes, policy and limits,
closed owned groups, no native/model/fixture inference, exact nonnegative charge
sums and full remaining metadata25+entry65+native62.5+SUP120+final45 funding.
Primitive data must remain labelled component-only; no full-owner qualification
is inferred. Reject failed/pending/unreceipted/stale/mismatched P before freeze.

The new driver requires narrow phase-binding fixtures: valid current P reaches
the actual adapter unchanged; stale source input, broken proof links, failed/
incomplete primitive and inconsistent sums fail; lock prior is P.total and the
postfreeze delta contains metadata work only, including positive external
correction, never primitive spend twice. Freeze these fixture commands before
running them. They may form part of the separately funded metadata25 phase's
preflight, with all cost in that phase; no unmetered validation is permitted.
If validation is executed as a separate intervening phase instead, first close
and carry its cost into the actual current input. P is not a timeless balance.

Raw metadata cumulative must be actual phase-start current total plus metadata's
own charge. The completed postfreeze account retains that exact prior and
metadata-only current delta under hard_total_ceiling_s3600. Use existing canonical
freeze/launch-accounting helpers, not a copied raw-float component. No metadata
or numerical work proceeds on the basis of this direction alone.
