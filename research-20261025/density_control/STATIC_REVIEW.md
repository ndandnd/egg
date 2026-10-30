# Focused static integration review

25 October 2026. Reviewed the final ready `selector.py`, `run.py`, `PROTOCOL.md`,
the parent `RESOURCE_DECISION.md` and `matching_pool/NEXT_CONTROL_DECISION.md`.
Checked the narrow existing classical selector/scorer and common-backbone
dependency against the already inspected native model/solve/extract/replay APIs.
No imports, compilation, tests, hashes, metadata freeze, solver calls or native
execution were performed. Only this review note was written.

**Outcome: sufficient for the specified development pilot; no substantive static
API, selection, budget or physical-admission blocker found.** This is not an
execution pass or numerical qualification.

- Both arms freshly compute CA1 scores and obtain B, K and ordering from the
  unchanged common selector inside their own decision clocks. CA1 asserts exact
  equality with the ordinary retained flexible set. CoverCA1 recomputes the
  frozen three-cover union, protects B union C, fails before model construction
  if that union exceeds K, and fills in the same CA1 order. No quota increase or
  cover removal is introduced. Exactly K flexible modes and every original
  boundary mode are retained; the driver compares M/K/B/boundaries across the
  two fresh arms of each case without reusing their scores.
- Four assigned decisions have the declared alternating order. Each rebuilds
  and identity-checks its full original case. The original physical matrix has
  one streamed inventory; only excluded movement upper bounds become zero.
  Retained binaries remain free with lower zero/upper one, and row/column counts
  are checked after the pure pullout-count objective is installed.
- Each decision sets native seed 17 and reads it back before and after its one
  bounded solve. Native thread count and finite admissible incumbent are checked.
  One separate capture and unchanged extraction precede independent original-
  case replay, pool-membership and selected-pullout/vehicle/incumbent agreement
  under the existing BOUND_GUARD. Exact integrated supply cost is evaluated,
  not claimed minimized. Native fleet bounds remain arm-restricted.
- The preparation-30/native-90/final-120 deadlines share one anchor before case
  construction; native time is capped at 60. Receipt-inclusive master admission
  requires a durable independently checked witness within 120. Whole-process
  720 CPU/600 wall limits, closure reserve, persistent stop latch, fresh exclusive
  namespace and retained per-decision failures match the decision. A complete
  diagnostic can contain failed or infeasible-to-admit arms.
- Source binding includes the frozen cover source and the dynamically used
  `experiments.codex_offline_rank` backbone dependency, alongside actual imported
  egglab sources, once per consumed file. Selection, mode, cover, bounds,
  inventory and capture artifacts remain separate for compact postprocessing.

The parent still owns the external stop for blocking native calls; cooperative
checks and peak RSS observations are not hard real-time resource guarantees.
Equal cardinality/B and a single seed on two exposed timetables diagnose this
specific candidate-density/structure question. They do not establish robust
superiority, generalization, learned electricity-information value or a fair
comparison with historical default-seed outcomes. Preserve all four outcomes and
the separate competence gate without retry or adaptive selection changes.
