# Pending budget proposal: resource review

Read-only review confirms the arithmetic and bounded scope. Current carried
charge587.8814716266195s leaves132.1185283733805s before the existing720s dispatch
stop, insufficient for eight32.5s allocations totaling260s before overhead.

The proposed total0.5CPUh equals1800s, adding900s (15CPU minutes) to the existing
ceiling. Retaining180s shutdown reserve gives1620s dispatch stop. The proposed
envelope is587.8814716266195 +20 administration +32.5 check +32.5 freeze +260 tasks
+520 monitor/supervision allowance +10 analysis =1462.8814716266195s,
leaving157.1185283733805s before the proposed dispatch stop.

Scope remains one local single-thread worker,5GiB RSS, the same two engineering
cases/eight tasks/seed/tariff and original stage/end/outer clocks. Every old
charge/failure remains carried; unused allowance permits no extra task or retry.
The patch changes only ceiling/dispatch constants and remains unapplied.

**Status: pending user decision.** Current900/720/180 limits remain authoritative.
This review authorizes neither the patch nor any check, freeze or native launch.
After approval, the changed policy needs its prospective source-bound check and
fresh lock/output namespace. No executions or source edits were performed.
