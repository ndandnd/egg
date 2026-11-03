# Frozen local campaign analysis

`analyze_local_campaign.py` implements the existing v2 protocol; it imports no model,
solver, or experiment modules. It never changes run artifacts. Default execution first
checks that every planned task has an attempt and terminal supervisor receipt, using
file presence only, and refuses outcome reading if the cohort is unfinished. Optional
`--allow-incomplete` permits explicitly requested descriptive diagnostics; incomplete
cohorts cannot pass promotion gates and no model recommendation is emitted.

The lock supplies exact arms, cases, grouping and paired seeds. Task IDs and block
ordering reproduce the frozen runner. Unknown directories, malformed receipt JSON,
wrong task/lock mappings, missing worker/replay receipts and unknown resource fields
are reported conservatively. A valid endpoint requires BOTH worker accepted_valid and
supervisor endpoint_valid, no censoring, a positive replay_ok flag in the stored
independent replay receipt, a finite exact bill, and no receipt/schema/infrastructure
issue. A worker-accepted but supervisor-censored plan remains censored, even where
future timing corrections could alter its treatment. There is no retrospective
correction of v2 timing. This analysis verifies stored admission evidence; it does not
independently rerun physical replay or reconstruct missing plans.

Qualification emits a complete cell health table and arm/status counts, resource and
failure accounting, and an engineering pass flag. It computes no economic ranking,
paired bill effects, bootstrap, or model promotion. Both-valid no-plan counts and
internal rejected candidates are retained. Worker exceptions are categorized; raw
tracebacks and stdout/stderr contents are excluded from outputs.

Screen economic effects use (control bill − v8 bill)/control bill only for positive,
finite, both-valid bills. Every group reports its paired denominator. Both invalid
is a failure-aware tie; one valid beats one invalid; these comparisons never supply
an invented finite penalty bill. Three seed-paired gains are reduced to a group median.
Group medians with fewer than three usable pairs are shown conditionally, with their
actual denominators, but cannot count as positive groups for the 7/10 gate. Conditional
size medians include groups with at least one usable pair. The overall statistic is
the weighted median of group medians with equal weight per size and equal weight per
observed group inside each size; absent size information makes it unavailable.

Bootstrap samples whole groups independently within each size, keeping each group's
seed-paired reduction together. It draws 10,000 replicates using random seed 20261017
and reports 2.5/97.5 percentile order statistics plus the number of finite replicates.
Undefined group gains remain undefined when resampled; replicates lacking either
size are excluded and their count disclosed. This is uncertainty description, never
a significance gate or an independent-seed analysis.

The screen reports all protocol gates verbatim: integrity/accounting; complete cohort;
v8 validity counts versus nonlearned and random by size; <=1 validity loss per size
against nonlearned; >=8 fully paired groups per size; >=1% overall median bill gain;
nonnegative gain by size; >=7 positive fully paired groups per size; no paired
regression beyond 5%; and nonnegative overall gain versus random. All must pass to
advance only to a separately frozen recovery study. CatBoost/full4/cold are secondary
comparisons. Matching/exceeding v8 by the fixed newly trained CatBoost comparator is
reported as graph complexity not having earned its cost. No full-model generalization
claim or recommendation comes from this development cohort. A failed gate calls for
diagnosis and a prospective revision, not termination of the user's research.

Accounting sums each immutable task supervisor charged_cpu_s once, supervisor CPU
from each ledger summary, and freeze CPU for qualification. It reports peak measured
worker RSS and missing accounting. It does not infer exact aggregate memory from
unsynchronized per-worker peaks or add historical cumulative worker totals from
summary rows a second time. Native candidate rejection events are diagnostic even
if a later retained incumbent succeeds. Any corrupt native log is an integrity issue.

Outputs are `summary.json`, `SUMMARY.md`, and `artifact_hashes.json` in a new directory.
The hash manifest covers all input artifact/log files, including only SHA256 hashes
for private stdout/stderr, plus asset-lock and analysis-source hashes. No raw logs are
copied into the report. Reports cannot overwrite an earlier analysis directory.

Example, only after all qualification tasks are terminal:

```sh
python3 research-20261017/analyze_local_campaign.py --lock research-20261017/local-assets-v2.json --runs research-20261017/local-qualification-v2 --stage qualification --output research-20261017/qualification-analysis-v2
```

Use `--stage screen` with the completed screen directory for the substantive study.
Toy fixtures only were executed while preparing this analysis:

```sh
python3 research-20261017/analyze_local_campaign.py --self-test
```

Fixtures cover unfinished-cohort refusal before outcomes, parent censor overriding
worker acceptance, correct both-valid denominators, no promotion from a tiny partial
population, corrupt-receipt/unknown-accounting rejection, and private-log hash output.

Pre-screen correctness amendment: nonpositive bills remain valid physical endpoints
for failure-aware counts, but they make relative-bill promotion inapplicable. The
report records applicability and nonpositive both-valid pair counts per comparison;
promotion additionally requires positive bills at every valid endpoint in every arm.
Conditional descriptive medians remain labeled with their denominators and cannot
override these gates. Screen resource integrity requires known worker peaks within
5 GiB and no recorded worker/aggregate memory, sustained system-pressure, campaign
CPU, or campaign safety stop in any arm, including secondary controls. Unknown
resource fields fail closed. Toy regressions start with an otherwise passing full
20-group screen and inject zero/negative bills, secondary-arm nonpositive bills,
each safety-stop reason, excessive RSS, and unknown RSS; each blocks promotion.
Historical run receipts are unchanged.

V3 accounting amendment: qualification total additionally includes the asset lock's
`prior_qualification.charged_cpu_s`, including its locked conservative accounting
allowance. This amount is disclosed separately and is added exactly once; it is not
charged again to the separate screen envelope. V3 receipt health validates immutable
completion marker task, lock, shared monotonic anchor, result SHA256, and elapsed
materialization duration against supervisor endpoint wall. Missing, stale, or
inconsistent markers fail closed. Supervisor cleanup duration is excluded from the
decision endpoint. V2 analyses retain their original receipt interpretation and
require no new marker. Toy fixtures verify carry-forward arithmetic, timely
materialization despite later cleanup, stale/missing marker rejection, and unchanged
v2 marker-free health. No historical receipts are changed.
