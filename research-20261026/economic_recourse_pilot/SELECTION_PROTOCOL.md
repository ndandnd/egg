# Prospective frozen metadata-only cohort selection

Static gate review passed; PREPARATION_PROTOCOL.md records the exact prospective
source-pin and execution stages. `select_cohort.py` refuses before the sole
metadata input unless its separate launch is FROZEN/PASS. PREPARATION_FROZEN and
SOURCE_PINNED states still deny it. No actual metadata values/selected IDs were
read during source preparation. Parent must accept metered preparation and
freeze the carried prefix/control before the one selector command.

The only DATA input is the fixed closed
`research-20261025/fit_target_support/attempt01/receipt.json`. One capped
32-MiB read hashes its bytes once. Full JSON decoding is transiently allowed;
semantic projection is only top-level `receipt_complete`, `checks_passed`,
`support_report_complete`, and `groups[].group/base_id`. Other fields, including
target/availability/membership/cost/label metrics, are discarded without semantic
inspection. No referenced path is followed. All three flags must be true and
there must be80 unique canonical `physical_v2_s{base}` IDs, integer10000–10127.

Use only the source-derived TRAIN assignment service projection:
`j=(7*(base-10000))%54; services=20 if(j//3)%2==0 else28`.
This reproduces the declared service component of
`physical_learning_cases.assignment`, not a claim that a metadata receipt stores
trip counts. The original stored profile and trip count must match later or the
assigned cohort fails admission without replacement.

Uniformly exclude the whole earlier pilot union
10001,10002,10018,10006,10009,10010,10015,10005. Sort the remaining actual FIT
base IDs ascending, select first2 per20/28 profile, order the20 pair then28 pair.
Missing or insufficient metadata stops selection. No advance to another ID
after any later difficulty. All are exposed FIT development groups; no namespace
alias closure, model-training independence or final-generalization claim.

Fresh exclusive `selection01` preserves partial/failure receipts. Source and
this protocol are read/hashed once against parent-frozen pins; launch bytes are
read once and their consumed digest recorded. Exact command and initial prefix
are prospective; metered preparation fills source pins and parent adopts its
external charge before selector freeze. An optional existing input pin may be frozen; absent
one, consumed bytes are bound by their once-computed digest and the mandatory
prospectively named tracked version. `input_version` must contain the literal
repository root and repository-relative receipt path, a full40-hex Git revision,
and `freeze_assumption: tracked-receipt-unchanged-from-named-revision`.
The gate requires that descriptor before input and records it in the receipt.
The closed receipt is immutable under standing policy; the named tracked version
is frozen prospectively. This is an explicit freeze assumption, not a new Git
subprocess or independent working-tree comparison. A supplied preexisting SHA is
compared with the consumed once-computed digest; it cannot substitute for an
absent version descriptor. The named tracked version is21bd18e8fdedfbb4895c8e21008df1fd68ad50ec.
No original rows, plans, cases, generators, project imports, optimizer, replay,
children or model assets are used.

Total10 CPU/30 wall, body5/20 and publication reserve5/10, one stdlib process,
one Python thread and observed self RSS<=5GiB. All startup/publication/exit are
inside total; the external meter makes the final resource decision. The receipt
contains prepublication observations and pending external acceptance. This
separate stage is INSIDE the campaign120 preflight/2400 total, not additional
funding. Main owner adopts its external retained charge and elapsed once through
the later frozen cohort-admission descriptor; no duplicate charge or old-budget
reset. No automatic main launch follows selection.
