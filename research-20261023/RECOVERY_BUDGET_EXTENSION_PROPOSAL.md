# Proposed validation-budget decision — not authorized for launch

24 October 2026 UTC. **Pending user decision. No budget change has been applied.** The current admission/capture repair and revised check supervisor passed 118 solver-free tests with current sources bound to `admission-capture-checks-v2/attempt01`. Full native qualification remains failed/incomplete; these tests establish no 80-trip speedup, model quality or learned advantage.

## Why a decision is needed

The current heartbeat states that the native primitive and subsequent qualification share a hard **0.25 CPUh cumulative allowance**. Existing code enforces a **900-second** hard ceiling, **720-second** dispatch stop and **180-second** shutdown reserve. Complete carried charge is **587.8814716266195 seconds**, including all failures. Only **132.1185283733805 seconds** remain before dispatch stop. The original eight 32.5-second allocations alone need 260 seconds, before monitoring, source checks, freeze, replay or finalization. A complete unconditional repeat cannot fit.

## Recommended concrete change

Raise the **total** validation ceiling to **0.5 CPUh (1,800 seconds)**, adding at most **0.25 CPUh (15 CPU minutes)** to the previously authorized ceiling. Keep the shutdown reserve at 180 seconds, making dispatch stop **1,620 seconds**. Carry every previous charge forward; never restart the ledger. Keep one local single-thread worker and 5 GiB RSS; use no cluster, protected data, new timetable, training or comparison screen.

The exact proposed runtime policy diff is saved in `recovery-budget-extension-proposal.patch`; it is not applied. After an approving user reply, apply that two-number policy change, record a source-bound check under a fresh namespace, and review its receipt before a new external fixture/source freeze and native launch. No old lock, failed output namespace or raw log may be overwritten or analyzed with changed code.

Retain the original engineering matrix: cases50997/40 and50999/80; static restricted, full recovery, cold full and injected setter failure; seed17/day; nonlearned30%+top-three; eight tasks. Keep the original12/15/24/27/30-second stage/endpoints and32.5-second supervisory allocation. Do not substitute a case or lengthen a solve to obtain a pass. Use a fresh prospective native revision with immutable lock/argv/environment/library/fixture identities before dispatch.

## Resource envelope and decision criteria

The proposal can reserve 20 seconds of administration, up to32.5 seconds for a source-bound check, up to32.5 seconds for the external freeze, eight32.5-second task allocations, a deliberately conservative additional two32.5-second supervision/monitor CPU allowances per task, and10 seconds of analysis. Including all587.8814716266195 historical seconds, that envelope is **1,462.8814716266195 charged seconds**, below the proposed1,620 dispatch stop and1,800 hard ceiling. Actual measured/conservative charges remain authoritative; unused capacity authorizes no additional task or automatic retry.

Pass only with complete timely/accounted matrix, independent replay/exact bills, correct unrestricted-bound scope, native partial-start processing and retained valid fallback through the injected failure. Stop on the first engineering/resource/receipt failure; preserve any late candidate as a failed/censored diagnostic. Cap exhaustion is incomplete, never a pass. A pass establishes this engineering interface only, not ML/economic superiority. Future comparisons must apply a common frozen evidence policy across all arms.

If the user retains the0.25CPUh ceiling, do not execute this patch or promise a complete repeat. Continue useful offline design/analysis, and separately justify any smaller diagnostic within the remaining allowance without treating it as complete qualification. Do not ask the budget question repeatedly or silently reinterpret the existing cap.
