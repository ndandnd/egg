# Retrieval comparison runner review

**Verdict: reviewed; no blocking design or runner-contract issue remains in the frozen files.** The protocol fixes six development cases, three markets, four target arms, paired source runs, one target planner and one own-price response per case. The source and target pricing controls are fresh, with no imported pricing lower bounds, bound cache, or native MIP start. Target arms rotate across the six cases; all comparisons use the same admitted source pool. The scope supports a bounded development comparison, not held-out validation, learned-method evidence, or a general speedup claim.

Source admission ties each candidate to a source pricing request, result, global-bound event, checked physical column, projection key, witness hash, source identity, and native bound admission. A valid early column remains available when a later call is unresolved or the source child fails; the failed/late return and unmatched calls stay visible. Nearest-price uses the actual source-call price labels and target linear-price vector. Cheapest-bill evaluates exact stored-number `ops_cost + a·L` over that same pool with deterministic ties. Price-label ties for a shared physical projection are retained in pool provenance.

The import adapter is explicitly a `derived_feasible_pool_import` with `bounded` status. It canonically checks each selected payload against the admitted candidate, replays the fleet, rebuilds a target-market one-hot feasible upper, and records source file hashes, source states, price labels, selected keys, and policy in its lineage digest. It carries no source lower, gap, or solver statistics. Target hull assessments now bind reported lower and upper values to independently replayed certificate and mixture values. The own-price response requires an on-time planner result with a replayed witness and bounds; late and failed assessments remain visible but are excluded from primary metrics. Missing plan or interval fields remain unavailable.

The six-by-eight child matrix matches the 48-child design. Each child has its routine allowance plus a 30-second process margin; the frozen totals are 5,160 routine seconds and 6,600 child seconds, with a 6,900-second controller cap, 7,100-second supervisor/outer limit, and 7,200-second Slurm limit. The frozen runner records source-generation child time and controller pool-admission/build time once per case, target online child time, and explicit reuse amortization. Direct proposal and preparation artifacts are saved before target verification, so a later hard stop preserves the proposal and its timing. Late and failed assessments remain visible but are excluded from primary comparison metrics.

No public source archive, held-out group, solver, or cluster job was accessed or run for this review. Sol reports eight pure mocked tests passed, with `py_compile` and `bash -n` checks; I inspected the tests but did not rerun them. The work remains prospective until the separately authorized freeze and single pilot attempt.

## Reviewed pins

- `src/experiments/retrieval_comparison.py` — SHA-256 `7534692abd93bea7c0adef8cb353585b8bcc55bddb4fd87227e043f50b9a76d0`
- `src/tests/test_retrieval_comparison.py` — SHA-256 `f30923ffa47e71718f26c733e25da44d0439ab7dca8ec4bbc80b58275940922e`
- `src/cluster/retrieval_comparison.sbatch` — SHA-256 `eda3f1c205f5927074a77e90048260c195d53b0965ec3ca68923db73d2753eae`
- `research-20260928/retrieval-comparison/RUNNER.md` — SHA-256 `1d19a2a70a5a1a9dfef1cbd9b803ee520c56ee64ef1a4f95439c4957823293a1`
- `doc/RETRIEVAL_COMPARISON_PROTOCOL_20260928.md` — SHA-256 `a65326dfb61ab34819b8912323b3fdd7f9243db4c89caa751d6b323a0be60c99`
- `src/experiments/native_scaling_cases.py` — SHA-256 `faed7a5b122c6ed233aac75b2f4e54044b006e1bf56139a729d4a875fa2d5c2f`
- `research-20260928/retrieval-comparison/GENERATOR.md` — SHA-256 `8291a880e216a9af18be5a1aa25b03ade9d098af4f3e91703f52d6f378adf6e1`
- `research-20260928/retrieval-comparison/SYNTHETIC_PREFLIGHT.json` — SHA-256 `b68ef2e194b005802916a40ad72a98dc2bd2bdc7b123897e6e2c0350eaddc60c`
- `data/public/sistig_26088190_v1/eberbach_native_case.json` — SHA-256 `5ffb2f3a322b40c9c6c56972607fd0c4b21130cd35cd08e0a465f34fba67dc19`
