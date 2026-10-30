# Exploratory source-route model pilot: replay review

This is an eight-group TRAIN-only movement-classification pilot. Each positive means an edge occurred in a physically replayed observed source incumbent; a negative means it was unchosen, not infeasible or inferior. Results are out-of-group cross-validation on training groups, not independent development/test performance, validated deployment, or route-cost gains.

The admitted dataset has 8 independent base groups and 16 source fleets (7560 candidate movement rows). The pilot used 12 tasks: four group folds × three repeated seeds. The 12 tasks are not 12 independent datasets. Dataset receipt SHA-256: `c9ed1e67356812e60a5986153227029d8eb15e98e2799a0ef87a56284be671d7`.

I recomputed held-out and training probabilities from the serialized model weights and preprocessing, using only the admitted `cases.jsonl` and `source_inputs.jsonl` plus saved task artifacts. No fit, native solve, target outcome, or development/test table was read. Saved movement probabilities, metric summaries, and training-curve endpoints were checked against the recomputation.

## Held-out metrics

Metrics average the three seeds within each base group, then average the eight group scores equally. Recall denominators include only groups containing that class.

| Method | Log loss | Brier | Accuracy | Positive recall | Negative recall | Positive rate |
|---|---:|---:|---:|---:|---:|---:|
| Training prevalence | 0.2307 | 0.0575 | 0.9388 | 0.0000 (n=8) | 1.0000 (n=8) | 0.0612 |
| Training kind frequency | 0.2079 | 0.0550 | 0.9388 | 0.0000 (n=8) | 1.0000 (n=8) | 0.0612 |
| Linear logistic | 0.2571 | 0.0628 | 0.9388 | 0.0000 (n=8) | 1.0000 (n=8) | 0.0612 |
| 16-unit tanh MLP | 0.2083 | 0.0527 | 0.9388 | 0.0000 (n=8) | 1.0000 (n=8) | 0.0612 |

The raw candidate-row selected-edge rate is 5.7%; the group/fleet-weighted mean is 6.1%. At the fixed 0.5 cutoff, every method predicted zero positive edges across the held-out predictions (0 MLP positives over 22680 row evaluations including repeated seeds). Positive recall is therefore zero and negative recall one for all methods: the 93.88% accuracy is the all-negative result, not useful route-proposal quality. The MLP improves Brier from 0.0550 to 0.0527, but its log loss (0.2083) does not beat kind frequency (0.2079); the linear model is worse on both proper scoring metrics. This small pilot shows no clear model advantage. No threshold was tuned on held-out labels.

## Training versus held-out fit

Training loss is averaged over seeds within each of four overlapping fold-training sets. Held-out loss is seed-averaged within each of eight groups, then group-averaged. These small gaps are descriptive only; they do not establish adequate training or the absence of overfitting, and they are not independent uncertainty estimates.

| Method | Training log loss | Held-out log loss | Held-out minus training |
|---|---:|---:|---:|
| Training prevalence | 0.2302 | 0.2307 | 0.0005 |
| Training kind frequency | 0.2069 | 0.2079 | 0.0010 |
| Linear logistic | 0.2581 | 0.2571 | -0.0010 |
| 16-unit tanh MLP | 0.2080 | 0.2083 | 0.0003 |

## Reproducibility and limits

All 12 task and wrapper receipts completed. Maximum saved-probability discrepancy was `1.67e-16`; maximum metric discrepancy was `7.42e-14`. Per-task model/runtime/source hashes and wrapper receipts are recorded in the machine-readable review. Scheduler accounting recorded 100 allocated CPU-seconds and 26.05 receipted model seconds; each task received one CPU and 8 GB. Worker elapsed times sum to 26.1 seconds across concurrent tasks; the slowest task wrapper took 4 seconds. The worker-time sum is not elapsed campaign time.

The metrics assess how well fixed, shallow scorers classify edges from observed source incumbents. They do not measure a decoded route, physical feasibility of a new proposal, target cost, global optimality, or speedup. Any ranking plus constrained decoder should be specified prospectively and evaluated on route feasibility and cost; do not tune a threshold on these held-out labels. The 8-group pilot remains exploratory; later learning checkpoints use predetermined training-group prefixes and preserve development/test groups.
