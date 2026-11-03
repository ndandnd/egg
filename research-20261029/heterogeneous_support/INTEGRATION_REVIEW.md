# Heterogeneous-support qualification: source integration review

29 October 2026. Read the seven requested new source/protocol/literal-control files, with a focused follow-up read of the comparison routine. No execution, imports, compilation tests, hashes, empirical data, native solver, commits or subagents. This review concerns only the eight-case n-connector model; no pending single-shared-connector extension is incorporated.

## Decision: scoped source PASS after minimal owner repair

No scientific/source defect found in the intended independent comparison. Actual implementation qualification remains pending. `LAUNCH.DRAFT.json` is not launch authority; the separate actual FROZEN control and source commit remain required.

I minimally repaired NEW `run.py` before freeze: guard/validate master decoding and the exact eight-case ID/status ledger; preserve explicit UNKNOWN_UNREPORTED rows on absent/unreadable results; move owner resource observation after complete packet reading. The previously unguarded malformed-master path could prevent the closure receipt. No theorem/reference/candidate/verifier behavior or cases changed. Parent was notified of this repair.

## Independent formulations

The reference enumerates every partial bipartite matching recursively, retaining labels. Its physical model derives per-bus early nonnegativity/power, after-A headroom, after-service nonnegativity, terminal-demand bounds and grid capacities from raw SOC equations with full terminal refill eliminated algebraically. Active-row vertex enumeration is exact and generic; it does not call matching thresholds or the discrete-convex criterion.

For every raw vertex the reference constructs a charging witness and replays coverage, per-bus inventory, simultaneous grid draw, individual power and each connector's occupancy. Terminal grouping of paired buses and unmatched A/B buses relies on the declared cross-sum≤30 and n30kW connector class. It does not claim to solve arbitrary connector scheduling. Every assignment's early projection is minimized continuously; hull cost comes from generic convex hull geometry and scalar minimization, independently of candidate interpolation formulas.

The candidate's subset DP retains optional unmatched As and one use of each B. It computes minimum recharge thresholds by cardinality, then applies the proved scalar physical/hull formulas. A separate complete assignment enumeration retains actual matching ties and response sets. There is no reference import or shared threshold routine. Standard matching/convexification logic is still shared mathematical background, not evidence of independent discovery.

## Exhaustiveness, ties and continua

The comparison checks all matching labels, cardinality thresholds, every assignment's energy interval/cost and its entire individual-allocation box versus the raw reference polytope vertices. It compares all physical optimizer labels, prices, regret, full per-assignment fixed-price response intervals and the optimum allocation section at its exact energy sum. Strict convexity fixes each assignment's optimal aggregate early energy; the section represents all individual early allocations at that aggregate, rather than falsely enumerating a continuum as finitely many schedules.

When prices are equal, both methods retain the full minimizing early interval within each globally minimizing assignment; unequal prices choose the appropriate endpoint. Collinear generic hull vertices can be removed without erasing physical assignment labels. Repeated projected endpoints are consolidated for hull geometry only. The zero-threshold and flat-response cases exercise these distinctions. All-positive-fee domain restrictions avoid the known zero-fee counterexample to the strict-interior support criterion.

Eight literal cases are fixed both in `cases.json` and independent verifier literals/order. The comparison cannot silently replace a failing case or report only available outcomes. A fatal source/domain/reference error preserves its attempted failure and pads remaining case IDs as UNATTEMPTED. An ordinary comparison mismatch is retained and the declared remaining cases continue.

## Controls and smoke anchor

The source contains exactly18 negative controls: five result/set corruptions, three physical-witness corruptions and five invalid-domain calls for each of the two methods. The additional hand-derived smoke checks the nominal heterogeneous D, CH, gap and regret. A missing negative rejection enters failures and prevents PASS. Assignment-tie and flat-interval controls assert that their targeted degeneracies actually exist before trying to erase them.

The witness replayer uses exact interval integration, with fixed service boundaries included in its cut set. No charging overlaps a service on the same bus; nonnegative service drain and constant charge power make endpoint SOC checks sufficient within each elementary interval. It verifies exact terminal20 and total purchased energy. These are prospective controls, not successes established by reading code.

One dependency to keep visible: allocation-polytope comparison uses the reference's generic vertex enumerator on both the raw and analytic descriptions. This is appropriate for comparing two independently derived polytopes, but does not independently qualify that enumeration implementation. Raw witness replay and the smoke anchor provide complementary checks; finite agreement remains implementation evidence, not proof of the theorem.

## Bootstrap, resources and interpretation

Scientific source/cases/protocol buffers are checked against the frozen commit and cached once in the metered worker; only cached reference/candidate buffers are executed. The fixed isolated `-I -S -B` command uses stdlib and leaves assertions enabled. No native/old-data import or retry exists. The owner refuses a non-FROZEN source authority and creates an exclusive new run directory.

Limits match the reviewed contract: package60CPU/90wall; worker hard40CPU, observed inclusive45CPU/60wall; owner soft5/hard50CPU, wait60wall, alarm87/cleanup3 and512MiB observed process RSS. Child usage overlaps the outer owner meter, not additional spend. Final external observation through publication/exit remains authoritative; no instantaneous aggregate containment claim is made. Missing/malformed worker results now preserve the administrative eight-state ledger and cannot produce owner success.

Successful qualification would establish that the independently implemented raw-SOC and threshold methods agree on all eight declared cases, ties/continua and controls. It would not establish novelty, population prevalence, public37-service support, scalability, ML benefit or the unreviewed shared-connector generalization. Preserve this scope in the eventual result report.
