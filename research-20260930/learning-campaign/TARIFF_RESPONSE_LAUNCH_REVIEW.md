# Frozen-model tariff transfer: prospective launch review

30 September 2026. This review precedes the single new tariff-transfer attempt.
The execution commit is recorded in its subsequent launch receipt.

## Scientific purpose

The completed charge-response experiment does not establish an adaptive model
advantage: ridge chose source 1 on all four development timetables, exactly
matching an always-source-1 rule. This prospective transfer experiment asks
whether that frozen model responds usefully to tariff changes. It introduces
always-source-0, always-source-1 and training-majority controls before observing
any new target outcome. It does not refit the model to the preceding results.

Four new development timetables each receive late-cheap, day-cheap and flat
tariffs with the same nominal mean across their 30-hour horizon. There are four
independent groups, not twelve. The daytime discount intersects intermediate
depot visits; moving a discount only within the terminal refill window would
not test that distinction. These are exploratory tariff shifts outside the
model's original training tariff. Reserved independent test seeds stay untouched.

## Bounded review

- Sol implemented the runner, protocol, wrapper and seven focused pure tests.
  The tests cover grouped ordering, resource limits, reserve exclusion, tariff
  identities, training-only majority, target-outcome exclusion, preserved failed
  inference and frozen input hashes. All seven passed. Pure design generation,
  shell syntax and whitespace checks also passed; no local native solve ran.
  The freeze covers 27 source files and seven archived input hashes. The final
  summary includes a per-timetable mean paired excess across all three tariffs,
  left unavailable if any paired outcome is missing.
- Energy independently reviewed the novel risks and found no launch blocker:
  case/variant/source identities match, training-majority uses only the six
  archived training groups, both models are loaded without fitting, and all
  twelve choices are frozen before target outcomes. Inference failure retains
  independently runnable charging LP and cold controls. Failure status and
  physical feasibility remain separate; acquisition and chosen-LP times remain
  distinguishable.
- Luna independently checked the prospective protocol and wrapper. The design
  has 44 serial cells plus one capped inference step; no resource, reserve or
  constant-control discrepancy was found. Root reviewed the protocol, wrapper,
  launch guard, source/input freeze and result-summary boundaries.

## Limits and launch decision

The batch requests one CPU, 8 GB and 100 minutes; uses one native/BLAS thread;
has no retry/requeue; and excludes `scaglione-compute-01`. Child, inference,
controller and shell limits are 100, 60, 5400 and 5700 seconds respectively.
Eight source acquisitions are shared across variants, followed by 24 charging
LPs and twelve cold controls. The fresh checkout and exclusive attempt guard
prevent accidental duplicate submission. Existing other-project jobs and held
jobs are not modified.

Launch one attempt after the reviewed source and protocol are backed up.
Interpret paired excess only within the paid two-candidate pool. Linear-tariff
charging labels are not nonlinear/global optima. Keep provisional labels,
failures and all spent time. A constant choice matching the model remains a
negative result for adaptive selection, even if individual candidates improve
on cold incumbents. No global speedup claim follows from model completion.

Commands reported by the implementation worker:

```sh
PYTHONPATH=src python3 -m pytest -q src/tests/test_tariff_response_campaign.py
bash -n src/cluster/tariff_response.sbatch
git diff --check
PYTHONPATH=src python3 -m experiments.tariff_response_campaign design >/tmp/egg-tariff-response-design.json
```
