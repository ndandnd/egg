# Independent static review: pricing-start pilot runner

**Verdict: no blocking runner or protocol issue found.** The frozen runner is suitable for the root-controlled preflight/launch step. This is a prospective, development-only fixed-price oracle diagnostic; it is not evidence of a pilot outcome or a whole-hull speedup.

The runner binds the exclusive attempt to the clean execution commit, source hashes, protocol, source inventory, runtime versions, and the effective seed/backend observed from a lightweight model without optimization. It admits only the four pinned same-case physical plan pools: raw and receipt hashes, original status/identity/paid time, and every candidate column's physical replay and compact-start validation are checked. It does not reuse historical cache-bound evidence. A missing or invalid pool makes both arms in that pair ineligible, with no replacement or fallback.

The frozen design has 4 cases × 2 predeclared price queries × 2 arms (16 calls), with deterministic source-plan selection and counterbalanced within-query order. The same known source-plan upper is retained for both arms. Each call has its own process/model, predeclared cap, receipt, and raw files; the controller does not retry. Setup submission/rejection/timeout events are retained by the start-aware reader, while native acceptance remains unknown. A no-plan raw lower stays diagnostic and cannot enter an admitted interval; the common source upper, replayed native incumbent, and admitted native interval remain distinct.

Failure handling preserves partial receipts/events and reconciles all declared rows. The supervisor waits for process-group quiescence, rechecks frozen inputs, then seals the attempt. In the batch wrapper, `SETUP_SECONDS` is sampled immediately after preflight and before supervision, while whole-wrapper elapsed time is recorded separately. The protocol also keeps historical source generation and one-time preparation costs separate from conditional online child time. No platform/hostname match is required for runtime equality.

Validation recorded by the implementation author: 10 focused pure tests passed; `bash -n` and `py_compile` passed; non-optimizing admission/replay of the four existing source pools succeeded. I reviewed the final source and protocol statically and did not rerun those checks. No pilot was launched as part of this review.

Reviewed pins:

- `src/experiments/pricing_start_pilot.py` — `0efaa2fa49eee3d979bdc1569e26bbe2c98d5785f11f9602a001cad185e35937`
- `src/tests/test_pricing_start_pilot.py` — `7662dc4d03041bcc3d147c8dffcf8a3d6d28c1e56605a79a455ca5cf2289a2f7`
- `src/cluster/pricing_start_pilot.sbatch` — `a6ec5d37f75db91a45dec1e3a4665fee3ece37900fb4638733577d813eb0425a`
- `doc/PRICING_START_PILOT_PROTOCOL_20260928.md` — `f4f8489e9e2fd59479810d2fa53d85b420c6f3546d6864a2de720943645195a3`
- `research-20260928/pricing-start/SOURCE_INVENTORY.json` — `1b12a6ac3277c6eea4ff5919d904e1fcf9239195db3486945e492c56b31e5342`
- `research-20260928/agent-notes/pricing-start-runner/IMPLEMENTATION.md` — `bdd7cd8143f46a71957223e818eb776b3ee1f231d2e54d9d18814215733f90cf`
- `research-20260928/pricing-start-pilot/README.md` — `14e1c7fa6e51468b67bfd0e408c6690ef27f18348369fd4ec1e3282f3900e172`
