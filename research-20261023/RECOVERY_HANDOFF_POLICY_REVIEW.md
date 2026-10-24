# Prospective handoff policy review

24 October 2026. Conceptual review only; no execution, runtime import, solver, source/protocol edit or retry. V6 remains failed at2/8 under its strict13/25 handoff rule. Its later candidate cannot be reclassified retrospectively.

## Recommendation

For a future global anytime interface, treat13/25 as **planner budget targets**, with15/27 as hard independent-admission limits and30 as the hard output endpoint. This is principled if prospectively declared for every arm: stop native search/completion at their declared effective deadlines, retain a candidate returned by nonpreemptive postprocessing only if independent full replay, exact billing and required durable admission actually finish within the hard limit. Retain an earlier admitted fallback on every subsequent failure. This evaluates what the entire method delivers within a common hard clock rather than whether an internal function returns exactly on target.

It does change the V6 contract. The nominal2-second gap becomes a **planned headroom allocation, not guaranteed reserve**. Postprocessing may consume it. Calling that unchanged strict reservation would be misleading. The requested policy permits overrunning a planning target; it must never permit native time-limit renewal, a later admission/output endpoint, skipped replay, a fresh per-stage completion allowance or an uncharged capture path.

The given V6 full planner returned26.0151, leaving approximately0.9849 s before27. That creates an opportunity for timely admission, not proof that independent lift, copy, save and bound admission would all finish. No counterfactual success should be claimed. A future task must perform those operations and record their actual endpoints; late first saves remain unadmitted artifacts, and late bounds remain unavailable.

## Minimal contract distinction

- Keep the native planner deadline13/25 and planned integer stops10/22, bounded by original12/24; cumulative fixed-topology completion remains3 s. A target overrun grants no new native call or remaining-time reset.
- Log planner return/target overrun and remaining hard-admission headroom for every return, including no-plan/bound-only results. Target overrun alone is diagnostic under the new policy; replay/storage/backend/capture-reference errors remain errors. Do not broadly suppress `TimeoutError` or relabel post-build exceptions as expected typed pre-build stops.
- Permit outer admission only before15/27, then require actual lift/copy/save endpoints within15/27. The launch check cannot guarantee completion of a nonpreemptive operation. On overrun, retain only an earlier timely fallback, report the timing failure honestly, and preserve the original first-failure dispatch rule.
- Recovery prefix may consume headroom up to15, reducing the remaining full-search window before22. Controls use the same effective native deadlines, hard admission/output rules, evidence policy and total accounting. No arm receives compensation for larger captures or slower replay.

## Why this is preferable to another constant adjustment

Earlier native termination can create more expected headroom, but the observed39.78 MB warm capture and variable postprocessing show why subtracting another trace-specific fraction cannot establish a universal bound. Capture size scales with matrix/rounds and can differ across arms. Keep full evidence once and compact references, instrument its measured cost, and freeze a common evidence policy; any future capture budget or truncation policy needs explicit integrity/failure semantics. A smaller log is engineering overhead reduction, not learned-value evidence.

A soft planning target with hard end-to-end admission is the more robust method definition when postprocessing is not preemptible. If strict guaranteed reservation is scientifically required instead, retain V6's rejection rule and establish a conservative workload-dependent postprocessing envelope or an earlier native cutoff; current traces do not establish that envelope. Either choice needs a fresh source-bound policy/check/lock and deliberate remaining-budget review. This review authorizes no dispatch.
