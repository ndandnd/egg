# Fixture descriptor JSON representation check

This new package isolates the serialization defect diagnosed in the closed
adjacent_nonlinear_pilot attempt01. It does not reopen that attempt or change
its frozen source, admission, spending, six assignments or failed status.

The only repair is a pure helper comparing complete fixture descriptors after
normalization to their JSON wire representation. It preserves values, fields
and ordered lists. It does not replace the old canonical whole-record identity
function. Ambiguous mappings or unsupported values must not silently lose data.

Inputs are the new check, helper, this protocol and a frozen launch manifest.
There are no experiment, metadata, bank, fixture, source-plan or model inputs.
Literal examples contain hour keys 2 and 10, prices, ordered duties and battery
capacity. Check the old serialized comparison rejects an unchanged round trip,
the repaired comparison accepts it, and changed prices, missing hours, reordered
duties and changed battery remain unequal. This is a representation check,
not native, physical or economic qualification. A failure stops without retry.

Before execution the parent records one reviewed source commit, freezes the
manifest's exact command/revision and backs them up. The process hashes its
own consumed source/protocol/manifest buffers once. No separate hash audit,
project/sibling import, generated fixture, native backend, subprocess or network
is permitted. The new helper may be loaded by the pure standard-library check.
The output directory is created exclusively and may not be reused.

Selected NEW allowance is 5 CPU seconds / 10 wall seconds, including startup,
imports, source admission, checks and publication: body 3 CPU / 7 wall, closure
2 CPU / 3 wall. One process/thread, no child; OS total CPU/wall limits and
explicit phase checks bound the work. The external process meter and internal
prepublication meter remain distinct. No charge is refunded on failure.

Command shape, from the repository root, is /usr/bin/time -p -o
research-20261026/descriptor_wire_repair/process-time.txt .venv-local/bin/python
-I -S -B research-20261026/descriptor_wire_repair/check.py --source-revision
FULL_SOURCE_REVISION, with stdout/stderr in the same new package. The exact
full command is frozen in LAUNCH.json after focused review, before execution.

A passing check establishes only the helper's literal JSON boundary behavior.
Any later integrated run requires its own exact bank/receipt field authority,
versioned caller, source/command/resource freeze and fresh namespace. The
existing prepared bank's admission can be explicitly transferred; arbitrary
cache trust and repeated all-column replay are not substitutes for that rule.
Joint common and selected-fleet physical admission remains necessary.
