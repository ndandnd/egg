# Fresh CF1 implementation: one affected source check

24 October 2026. This is the source phase of CF1_FRESH_MECHANISM_PROTOCOL.md,
not a native launch or a new experiment allocation. Historical v3/v4 files,
failed ledger, receipts and cumulative spending remain unchanged.

The new cf1_entry_repaired wrapper must use restored serialized bindings to
reuse v4's ACK observation and analyzer unchanged. Its singleton task, policy,
worker argv, source-check identity and exact paths must agree. The actual checked
entry preparer must run before the controller; no legacy prefix fallback is
permitted. Run requires an externally owned entry gate and independently supplied
lock/freeze/account roots. Its owner helper must charge the7.5s conservative
entry allocation exactly once, validate the real resume prefix, require live
owner evidence and check a short-lived permit again at the final worker Popen.
The final funding check must preserve the prelaunch prefix plus only the original
one-launch intent, because a live, unterminated attempt is not resumable.

The owner mechanism operates under the existing trusted frozen-source and known
spawn-channel assumptions. Register permitted synchronous monitor processes;
reject unexpected or detached entry spawns, incomplete observations, stale or
wrong identities, excess cost and expired permits. Known monitoring after native
handoff must retain the original worker clocks and cannot inherit the entry
deadline. No claim of containment against hostile code or arbitrary OS escape
is part of this research protocol. Source review must resolve concrete code-path
coverage and suffix-accounting issues rather than presume they are qualified.

Selected source implementation retains2.5s of the7.5s entry charge as conservative
handoff suffix. Its physical-CPU envelope caps the permit from the controller's
actual resource-report time as well as the owner's issue time; the permit may
last at most0.1s and must still be valid at Popen. The pre-suffix body uses actual
reported self/reaped-child CPU, parent OS samples, elapsed time and owner/monitor
CPU rather than assuming every physical core was busy throughout imports.
Post-handoff monitor reaping emits bound cumulative resource statuses. The owner
checks monotone identities/resources, status age at most0.25s, its own15s maximum
inside supervision45, live conservative whole-package funding, remaining native
allocation and30s final reserve plus1.5s cleanup. Terminal reconciliation remains
required; it cannot substitute for this live guard. Long finalization without a
fresh status conservatively fails that guard; this operational behavior is not
yet runtime-qualified and must not be interpreted as poor CF1 or ML quality.

## Frozen source-phase budget and scope

- Carry1527.8351450899538s from launch-entry-checks/accounting.json. ADMIN0;
  every earlier failure/reconciliation/preservation charge is retained.
- Source-phase hard20s, absolute end1547.8351450899538. Work10, outer12.5,
  inclusive check15, parent closure5; one single-thread child and5GiB monitored
  RSS. This20s is INSIDE the prospective175s package ending1702.8351450899538;
  it is not an additional allocation beyond that package.
- Global TOTAL1920/dispatch1740/shutdown180 remain unchanged. This source-phase
  end also lies below historical1620. No reset, credit or comparison-budget use.
- Exclusive cf1-entry-repaired-checks/attempt01; policy cf1-entry-repaired-v5,
  revision5. Sole executed test file test_cf1_entry_repaired.py. Eight qualified
  historical tests are byte-hash dependencies only, never a repeated matrix.
- Bind all current experiment/egglab Python sources, the sole test and qualified
  tests, retained monitor helpers, fresh decision/design notes, implementation/
  owner/review notes, this protocol, wrapper note, driver and exact prospective
  command/budget. No source edits during execution. Source/check identities in
  attempt and result must agree with the actual sole command.
- Tests use inert bindings, fake execution/clocks/process observations and
  handwritten temporary metadata. Standard-library socket units are permitted;
  no solver, model, fixture, real metadata freeze, native worker or cluster access.
  Exercise fresh identity and original ACK/analyzer delegation; nesting/thread
  rejection and restoration on exceptions; worker argv; preparation/precharge/run
  ordering; actual ledger/resume handling; one-use owner/permit identities;
  missing/late/unfunded/incomplete owner evidence; final Popen and post-handoff
  monitor behavior. Clearly state which production bodies are AST-loaded/faked
  rather than implying a real supervised controller was qualified.

Independent source review and prospective command/source/budget binding must
precede the sole invocation. Use run_cf1_entry_repaired_checks.py, which preserves
the reviewed ownership, monitoring, cleanup, reaping, audit and charge logic.
Initial and final inherited proof hashing reads already bound bytes, not research
inputs for analysis. Charge the full conservative internal computation, positive
whole-process reconciliation with0.02s precision, and finalization/preservation.
Preserve exact immutable source bytes; identical old snapshots may be reused.

A source-authoring substitution helper initially rejected a mismatched expected
scope string before creating its target file. The literal was corrected after
inspection. No project import, source test, attempt directory or experiment ran
in that authoring step. This is distinct from the one frozen invocation below;
no interrupted or unreceipted experiment is being retried.

If the sole check fails, preserve its complete evidence and all spending and stop
this attempt; diagnose before a new prospective source decision. No automatic
retry. A pass supports only the exercised fake/source behavior. It proves neither
real owner timing nor actual lock qualification, CF1 charging/replay/start
mechanics, full-problem bounds or ML quality. Review complete receipts and actual
headroom before separately freezing any later phase; no numerical dispatch or
metadata freeze is authorized by this source check alone.
