# Native-v3 80-trip static timing diagnosis

23 October 2026. Read-only diagnosis of saved task
`de8d8da71bc8d2dd1d5d` and relevant control/planner/lift source. No solver,
check, fixture, retry or runtime edit was performed. V3's failed outcome and all
raw receipts remain immutable. The parent owns the single analysis of all five
attempted tasks; this note addresses the fifth task's timing only.

## Observed timing

Times below are seconds from supervisor anchor `5990442.577138`.

| Observation | Elapsed seconds | Evidence/limit |
| --- | ---: | --- |
| Integer native dispatch | 1.934864333 | Recorded absolute dispatch time |
| Integer native return | about 24.061551291 | Dispatch plus recorded 22.126686958 elapsed |
| Candidate processing entry | about 26.787668251 | Inferred from end minus measured processing duration |
| Candidate processing end | 27.995570000 | `27 - wall_remaining_s`, where remaining is -0.995570000 |
| Result fsync endpoint | 30.383861875 | Completion marker; censored |
| Post-completion acknowledgment | 30.384752458 | Independent worker acknowledgment; late |
| Supervisor allocation end | 31.039251207 | Separate from the result endpoint |

The integer call was capped to the original anchor+24 deadline. Its observed
return exceeded that target by about 0.06155 seconds. There was no resource or
monitor failure in the supervisor receipt, and no native engineering event.

The approximately 2.72612-second interval between native return and candidate
processing entry includes incumbent capture and synchronous evidence work before
`_candidate`. `capture_incumbent` snapshots every native variable and mapping.
This task's captured event is approximately 23.94 MB in a normal JSON rendering.
The runner converts and durably appends it before forwarding it to the control
event list. Exact capture-versus-serialization/fsync durations are not separately
timestamped, so this trace cannot attribute that interval more finely.

Candidate processing itself took 1.207901750 seconds. Raw extraction and replay
produced an admitted candidate, but completion was attempted only after its
physical deadline and immediately reported `No time for fixed-topology
completion`. No fixed-topology native solve ran; cumulative completion spent is
zero. Candidate processing had already crossed 27 before subsequent objective
reconstruction/logging and before the planner could return. There is no explicit
planner-return timestamp; it cannot honestly be assigned an exact elapsed time.

## Additional work after the late planner

`control` calls `lift_plan` whenever the planner returns a plan, without first
checking the physical cutoff. That lift validates case inclusion, independently
replays the restricted source and full target, and recomputes the exact bill. The
clock check follows the lift. Here the lift returned, the check raised
`Control physical admission exceeded shared planner cutoff`, and the candidate
was discarded before durable fallback admission. Saved status is `no_plan`;
selected and fallback are absent.

The 2.38829 seconds from candidate-processing end to result fsync combine
remaining planner work, outer lift/replay, event serialization/append and result
materialization. Saved timings cannot isolate lift duration. Materialization
also appends the accumulated coordinator event list, including the already saved
incumbent, and serializes it into the result. The native evidence file is about
48.23 MB and the result about 21.44 MB. These are diagnostic overhead observations,
not measurements of solver CPU.

The failure therefore begins inside planner-side capture/admission and is then
aggravated by unguarded extra lift and repeated evidence materialization. It is
incorrect to attribute it solely to the extra lift. The saved record supports a
physically valid **late candidate**, not a valid timely task result. Neither its
bill nor the restricted bound can repair the censored endpoint retrospectively.

## Minimal prospective correction

First, check the physical cutoff immediately after planner return and before
starting outer lift. A late plan remains an explicit diagnostic and cannot become
a fallback or trigger more admission work. Preserve the post-lift cutoff check
as well, and record planner-return, lift-entry/exit and materialization timing.
This removes wasted work but cannot make an already late planner timely.

Second, retain one complete durable incumbent capture and use an identity/hash-
bound reference in accumulated control/coordinator events and result receipts,
instead of reserializing the same large payload. Preserve complete original
native evidence and fail closed on sink/reference failures. Any claim that this
fits the budget still requires a prospective checked revision.

If additional headroom is necessary, reserve capture, independent replay/lift and
durability time by shortening integer search **within** the existing 24-second
cap, with the same 27/30 physical/final endpoint. One trace cannot establish a
safe exact reserve. Do not lengthen time, change cases or bypass independent
replay to obtain a pass. No such correction or native retry is authorized by
this diagnosis alone.
