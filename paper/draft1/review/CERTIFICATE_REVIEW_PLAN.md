# Reader verification of the November draft

Before execution, freeze this plan and its adjacent local reader script together on the PR branch. Base paper revision b52d0c12657ec8fe47177693e2986fb12d6b1a65. The user requested a fresh independent assessment. A referee traces the rational bound independently. The parent runs each existing authenticated proof checker once in a fresh private directory. Source locations and exact trusted manifest digests are fixed in the script. This checks retained proofs on the existing host. Search, discovery and tuning are outside this operation.

Working directory is the paper-draft1 checkout. The only allowed input exports are the two specified under the archived checkout. The script skips the previous output. Each verifier authenticates its own inputs. If either fails, retain the failure and stop. No automatic retries. New inclusive allowance 300 CPU seconds and 360 elapsed seconds including copy, startup, two checks and output. Each checker has 120 CPU seconds and a 165-second parent timeout. Use one native thread. Check observed child RSS against 5 GiB and report the peak separately from the process meter. Parent and visual/review tool use outside measured commands is unknown.

```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 360; exec @ARGV or die $!;' /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/.venv-local/bin/python -I -S -B paper/draft1/review/check_public_local.py /Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261029 /private/tmp/egg-public37-pr57-review-20261102-a01 > /private/tmp/egg-public37-pr57-review-20261102-a01.stdout 2> /private/tmp/egg-public37-pr57-review-20261102-a01.time
```
