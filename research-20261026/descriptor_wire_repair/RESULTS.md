# Descriptor representation check — closed once

Source 96906ae1936ff6f3ac33cbd9a3536791f672ec36 and frozen control b8523e73
ran once, exit 0. All nine literal checks passed. Numeric hour keys 2 and 10
reproduced the old sorted-encoding mismatch; descriptor normalization made the
unchanged round trip equal. Changed price, missing hour, reordered duties,
changed battery, ambiguous key collision and scalar-encoding distinctions
remained rejected. No project, fixture, bank, model or native call was used.

The repair is isolated to the new descriptor helper. Frozen attempt01 and its
record-membership canonical identity remain unchanged. This is a regression
check for JSON representation, not actual-bank transfer, native compatibility,
physical qualification, an economic comparison or learned-method evidence.

The process used .03 displayed CPU seconds and .07 wall seconds. Internal
prepublication CPU was .037922, so retain .06 CPU seconds using the conservative
max(internal, displayed) + .02 rounded upward to .01 rule. Peak observed self
RSS was 20,398,080 bytes; one Python thread, no child. The selected new 5 CPU /
10 wall allowance is closed. No rerun or independent hash audit is needed.

Global closed process totals are 19931.13 displayed CPU / 20532.49 elapsed-sum,
retained tracking 19931.68 CPU. Legacy conditional guard 2546.091499549272 and
historical actual review CPU UNKNOWN remain separate. These are not exact
whole-session CPU, continuous elapsed or instantaneous memory containment.

Next is a separately reviewed integrated caller and explicit transfer of the
already admitted bank; source drafts do not authorize data reads or dispatch.
No scientific Google Doc append follows this check.
