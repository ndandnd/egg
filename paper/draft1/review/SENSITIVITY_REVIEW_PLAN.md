# Independent check of tariff intervals and physical assignment costs

The exact commands, working directory, source revision and fresh destination are in the adjacent shell script. Freeze them before any outcomes. Use the committed derived peak energies and all 9,472 original sensitivity cells at 81a7993b, the same observations as b52d0c12. All 18 original operator groups remain. At each of 300 and 400 kWh, use the original run eligibility, two midday capacities, four slopes and 37 offset values. Equal-length continuous offsets on the same interval give a design sensitivity, with each eligible operator and slope equally weighted. No sample selection or refitting follows the comparison.

Steps: independently derive exact offset intervals from decimal run-energy records, compare every historical grid label, regenerate the corrected study in a private copy, compare the complete new sweep rows to the frozen originals, and compare a generic linear assignment solver with the sorted formula at half and maximum cardinality for every eligible battery/operator pair. The deterministic tie counterexample is also checked. Complete output and failed stages stay in the fresh directory. Copy only necessary reviewer results into the paper after successful verification. No automatic retry. `make.sh` is not a certificate or raw-data verification stage.

Command, from the PR checkout, once after this control is backed up. Cap 240 CPU seconds and 300 wall seconds inclusive, one native thread, observed child RSS at most 5 GiB. Each stage is bounded separately. The external meter covers copy, startup, all children and reading the reports. Static and tool work is unmetered.

```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 300; exec @ARGV or die $!;' /bin/sh paper/draft1/review/check_sensitivity_local.sh > /private/tmp/egg-pr57-sensitivity-review-20261102-a01.stdout 2> /private/tmp/egg-pr57-sensitivity-review-20261102-a01.time
```
