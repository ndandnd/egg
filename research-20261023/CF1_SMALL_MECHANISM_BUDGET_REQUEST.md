# Decision: two additional CPU minutes for one bounded mechanism package

Current approval: TOTAL1800s, dispatch1620, shutdown180. All earlier failed and
conservative work is preserved; current charge1505.8511370494984s. Remaining
dispatch room114.1488629505016s cannot fit a robust run reservation137.5s
(worker62.5 + supervision45 + analysis/final30), even before source/freeze gates.

Request TOTAL1920s (32 CPU minutes, +120s), retain180s shutdown reserve and therefore
dispatch1740. One single-thread local worker,5GiB, no cluster; no automatic retries.
No change to60s physical/ACK endpoint,61s supervisor stop,62.5 outer allocation,
charging clocks, replay tolerances or start evidence. The new cap is not permission
for a comparison screen, training sweep or another80-trip deadline-tuning campaign.

The concrete prospective package uses the existing inspected50997/40 synthetic
fixture, CF1 seed17/day/no fault, explicitly distinct task/policy/namespace. Robust
planning: source15, freeze10, worker62.5, supervision45, analysis20, finalization10;
sum162.5, hard165 from the newest carry. At current charge its endpoint would be
1670.8511370494984, inside proposed dispatch1740. Preserve every failed attempt
and charge; stop after the one attempt if unsuccessful. Current source checks pass
and native entry is explicitly blocked pending this decision and a fresh source-
bound launch revision. Neither this request nor future approval bypasses those
engineering gates.

Purpose: determine whether actual fixed-route charging, durable replay-valid CF1
fallback and attributable native full-model start processing work on the inspected
small case. It provides no comparative or large-case quality claim. Full details
and independent reserve critique are in CF1_SMALL_MECHANISM_PROTOCOL.md and
CF1_SMALL_MECHANISM_REVIEW.md. If declined, leave native work blocked and continue
useful source/protocol analysis without repeating this request or historical gates.
